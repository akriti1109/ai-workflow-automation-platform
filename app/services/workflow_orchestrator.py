from sqlalchemy.orm import Session

from app.ai.providers import LLMProvider
from app.core.config import Settings, get_settings
from app.knowledge.embeddings import EmbeddingProvider, OpenAIEmbeddingProvider
from app.schemas.workflow import WorkflowResult
from app.services.ai_intent_service import interpret_user_request
from app.workflows.router import route_workflow
from app.workflows.context import WorkflowContext


def execute_workflow(
    db: Session,
    provider: LLMProvider,
    user_id: int,
    text: str,
    settings: Settings | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> WorkflowResult:
    settings = settings or get_settings()
    embedding_provider = embedding_provider or OpenAIEmbeddingProvider(settings)
    ai_result = interpret_user_request(text, provider)
    context = WorkflowContext(
        settings=settings,
        embedding_provider=embedding_provider,
        llm_provider=provider,
    )
    return route_workflow(db, user_id, text, ai_result, context)
