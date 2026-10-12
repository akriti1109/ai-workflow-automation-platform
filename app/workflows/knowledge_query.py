from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.schemas.ai import AIIntent, AIIntentResult, KnowledgeQueryEntities
from app.schemas.workflow import WorkflowResult
from app.services.knowledge_service import answer_knowledge_question
from app.workflows.context import WorkflowContext


def handle_knowledge_query(
    db: Session,
    user_id: int,
    original_request: str,
    ai_result: AIIntentResult,
    context: WorkflowContext,
) -> WorkflowResult:
    if not isinstance(ai_result.entities, KnowledgeQueryEntities):
        raise AppError("Invalid knowledge query entities.", 400, "INVALID_ENTITY")

    question = ai_result.entities.question or ai_result.entities.topic or original_request
    answer = answer_knowledge_question(
        db,
        context.settings,
        context.embedding_provider,
        context.llm_provider,
        question,
    )
    return WorkflowResult(
        intent=AIIntent.KNOWLEDGE_QUERY,
        success=True,
        status="completed",
        message=answer.answer,
        sources=answer.sources,
    )
