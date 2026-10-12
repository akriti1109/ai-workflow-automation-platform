from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.providers import LLMProvider
from app.api.ai import get_llm_provider
from app.api.knowledge import get_embedding_provider
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.knowledge.embeddings import EmbeddingProvider
from app.schemas.workflow import WorkflowExecuteRequest, WorkflowResult
from app.services.workflow_orchestrator import execute_workflow

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])


@router.post("/execute", response_model=WorkflowResult)
def execute_natural_language_workflow(
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
    provider: LLMProvider = Depends(get_llm_provider),
    settings: Settings = Depends(get_settings),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
) -> WorkflowResult:
    return execute_workflow(
        db,
        provider,
        request.user_id,
        request.text,
        settings,
        embedding_provider,
    )
