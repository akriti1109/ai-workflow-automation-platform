from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.ai.providers import LLMProvider
from app.api.ai import get_llm_provider
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import get_db
from app.knowledge.embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from app.schemas.knowledge import (
    DocumentUploadResponse,
    KnowledgeAnswer,
    KnowledgeDocumentList,
    KnowledgeQueryRequest,
)
from app.services.document_ingestion_service import ingest_document
from app.services.knowledge_service import (
    answer_knowledge_question,
    list_knowledge_documents,
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])
UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


def get_embedding_provider() -> EmbeddingProvider:
    return OpenAIEmbeddingProvider(get_settings())


@router.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> DocumentUploadResponse:
    content = await read_upload_file(file, settings.rag_max_file_size_bytes)
    return ingest_document(
        db,
        settings,
        embedding_provider,
        file.filename or "",
        file.content_type or "",
        content,
    )


async def read_upload_file(file: UploadFile, max_size_bytes: int) -> bytes:
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(UPLOAD_READ_CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size_bytes:
            raise_file_too_large()
        chunks.append(chunk)
    return b"".join(chunks)


def raise_file_too_large() -> None:
    raise AppError("Uploaded file is too large.", 413, "FILE_TOO_LARGE")


@router.get("/documents", response_model=KnowledgeDocumentList)
def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> KnowledgeDocumentList:
    items, total = list_knowledge_documents(db, limit, offset)
    return KnowledgeDocumentList(items=items, total=total, limit=limit, offset=offset)


@router.post("/query", response_model=KnowledgeAnswer)
def query_knowledge(
    request: KnowledgeQueryRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> KnowledgeAnswer:
    return answer_knowledge_question(
        db,
        settings,
        embedding_provider,
        llm_provider,
        request.question,
    )
