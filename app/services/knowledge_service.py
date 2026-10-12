import math
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.prompts import KNOWLEDGE_ANSWER_SYSTEM_PROMPT
from app.ai.providers import LLMProvider, LLMProviderError, LLMProviderTimeout
from app.core.config import Settings
from app.core.errors import AppError
from app.knowledge.embeddings import (
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderTimeout,
)
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.knowledge import KnowledgeAnswer, KnowledgeSource


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: int
    filename: str
    chunk_index: int
    content: str
    score: float


def answer_knowledge_question(
    db: Session,
    settings: Settings,
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
    question: str,
) -> KnowledgeAnswer:
    chunks = retrieve_relevant_chunks(db, settings, embedding_provider, question)
    if not chunks:
        return KnowledgeAnswer(
            answer="The available knowledge does not contain enough information.",
            sources=[],
        )

    prompt = build_knowledge_prompt(question, chunks)
    try:
        answer = llm_provider.generate_text(KNOWLEDGE_ANSWER_SYSTEM_PROMPT, prompt)
    except LLMProviderTimeout as exc:
        raise AppError("AI provider timed out.", 503, "AI_PROVIDER_TIMEOUT") from exc
    except LLMProviderError as exc:
        raise AppError(
            "AI provider could not answer the question.",
            503,
            "AI_PROVIDER_ERROR",
        ) from exc

    sources = [
        KnowledgeSource(
            document_id=chunk.document_id,
            filename=chunk.filename,
            chunk_index=chunk.chunk_index,
        )
        for chunk in chunks
    ]
    return KnowledgeAnswer(answer=answer, sources=sources)


def retrieve_relevant_chunks(
    db: Session,
    settings: Settings,
    embedding_provider: EmbeddingProvider,
    question: str,
) -> list[RetrievedChunk]:
    try:
        query_embedding = embedding_provider.embed_texts([question])[0]
    except EmbeddingProviderTimeout as exc:
        raise AppError(
            "Embedding provider timed out.",
            503,
            "EMBEDDING_PROVIDER_TIMEOUT",
        ) from exc
    except (EmbeddingProviderError, IndexError) as exc:
        raise AppError(
            "Embedding provider failed.",
            503,
            "EMBEDDING_PROVIDER_ERROR",
        ) from exc

    top_k = settings.rag_top_k
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        return _retrieve_with_pgvector(db, query_embedding, top_k)
    return _retrieve_in_python(db, query_embedding, top_k)


def build_knowledge_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    for chunk in chunks:
        context_blocks.append(
            (
                f"Source document_id={chunk.document_id}, "
                f"filename={chunk.filename}, chunk_index={chunk.chunk_index}\n"
                f"---BEGIN DOCUMENT CONTENT---\n{chunk.content}\n---END DOCUMENT CONTENT---"
            )
        )
    context = "\n\n".join(context_blocks)
    return f"USER QUESTION:\n{question}\n\nRETRIEVED CONTEXT:\n{context}"


def _retrieve_with_pgvector(
    db: Session,
    query_embedding: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance")
    rows = db.execute(
        select(KnowledgeChunk, KnowledgeDocument, distance)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .order_by(distance)
        .limit(top_k)
    ).all()
    return [
        RetrievedChunk(
            document_id=document.id,
            filename=document.original_filename,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=float(distance_value),
        )
        for chunk, document, distance_value in rows
    ]


def _retrieve_in_python(
    db: Session,
    query_embedding: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    rows = db.execute(
        select(KnowledgeChunk, KnowledgeDocument).join(
            KnowledgeDocument,
            KnowledgeChunk.document_id == KnowledgeDocument.id,
        )
    ).all()
    scored = []
    for chunk, document in rows:
        score = _cosine_similarity(query_embedding, list(chunk.embedding))
        scored.append(
            RetrievedChunk(
                document_id=document.id,
                filename=document.original_filename,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=score,
            )
        )
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    dot = sum(a * b for a, b in zip(first, second))
    first_norm = math.sqrt(sum(a * a for a in first))
    second_norm = math.sqrt(sum(b * b for b in second))
    if first_norm == 0 or second_norm == 0:
        return 0.0
    return dot / (first_norm * second_norm)


def list_knowledge_documents(
    db: Session,
    limit: int,
    offset: int,
) -> tuple[list[KnowledgeDocument], int]:
    query = (
        select(KnowledgeDocument)
        .order_by(KnowledgeDocument.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    count_query = select(func.count()).select_from(KnowledgeDocument)
    return list(db.scalars(query).all()), db.scalar(count_query) or 0

