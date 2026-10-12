import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.knowledge.chunking import chunk_text
from app.knowledge.embeddings import (
    EmbeddingProvider,
    EmbeddingProviderError,
    EmbeddingProviderTimeout,
)
from app.knowledge.extraction import extract_text, validate_document_file
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.knowledge import DocumentUploadResponse

logger = logging.getLogger(__name__)


def ingest_document(
    db: Session,
    settings: Settings,
    embedding_provider: EmbeddingProvider,
    filename: str,
    content_type: str,
    content: bytes,
) -> DocumentUploadResponse:
    safe_name = validate_document_file(
        filename,
        content_type,
        content,
        settings.rag_max_file_size_bytes,
    )
    text = extract_text(safe_name, content_type, content)
    chunks = chunk_text(text, settings.rag_chunk_size, settings.rag_chunk_overlap)
    if not chunks:
        raise AppError("No useful text could be extracted.", 400, "NO_EXTRACTED_TEXT")

    embeddings = generate_embeddings(embedding_provider, chunks)
    document = store_document_chunks(
        db,
        safe_name,
        content_type,
        len(content),
        chunks,
        embeddings,
    )

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.original_filename,
        chunks=len(chunks),
    )


def generate_embeddings(
    embedding_provider: EmbeddingProvider,
    chunks: list[str],
) -> list[list[float]]:
    try:
        embeddings = embedding_provider.embed_texts(chunks)
    except EmbeddingProviderTimeout as exc:
        raise AppError(
            "Embedding provider timed out.",
            503,
            "EMBEDDING_PROVIDER_TIMEOUT",
        ) from exc
    except EmbeddingProviderError as exc:
        raise AppError(
            "Embedding provider failed.",
            503,
            "EMBEDDING_PROVIDER_ERROR",
        ) from exc

    if len(embeddings) != len(chunks):
        raise AppError(
            "Embedding provider failed.",
            503,
            "EMBEDDING_PROVIDER_ERROR",
        )
    return embeddings


def store_document_chunks(
    db: Session,
    filename: str,
    content_type: str,
    size_bytes: int,
    chunks: list[str],
    embeddings: list[list[float]],
) -> KnowledgeDocument:
    try:
        document = KnowledgeDocument(
            original_filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        db.add(document)
        db.flush()

        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db.add(
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    embedding=embedding,
                )
            )

        db.commit()
        db.refresh(document)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to ingest knowledge document")
        raise AppError("Unable to ingest document.", 500, "DATABASE_ERROR") from exc

    return document
