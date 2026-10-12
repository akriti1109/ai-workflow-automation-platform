from sqlalchemy.orm import Session

from app.schemas.ai import AIIntent, AIIntentResult
from app.schemas.workflow import WorkflowResult
from app.workflows.context import WorkflowContext


def handle_unknown(
    db: Session,
    user_id: int,
    original_request: str,
    ai_result: AIIntentResult,
    context: WorkflowContext,
) -> WorkflowResult:
    return WorkflowResult(
        intent=AIIntent.UNKNOWN,
        success=False,
        status="unsupported_intent",
        message="The request could not be mapped to a supported workflow.",
    )
