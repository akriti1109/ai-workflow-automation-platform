from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    chunks: int


class KnowledgeDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class KnowledgeDocumentList(BaseModel):
    items: list[KnowledgeDocumentRead]
    total: int
    limit: int
    offset: int


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class KnowledgeSource(BaseModel):
    document_id: int
    filename: str
    chunk_index: int


class KnowledgeAnswer(BaseModel):
    answer: str
    sources: list[KnowledgeSource]

