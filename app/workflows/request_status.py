from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.schemas.ai import AIIntent, AIIntentResult, RequestStatusEntities
from app.schemas.workflow import WorkflowResult
from app.services.workflow_request_service import get_workflow_request
from app.workflows.context import WorkflowContext


def handle_request_status(
    db: Session,
    user_id: int,
    original_request: str,
    ai_result: AIIntentResult,
    context: WorkflowContext,
) -> WorkflowResult:
    if not isinstance(ai_result.entities, RequestStatusEntities):
        raise AppError("Invalid status lookup entities.", 400, "INVALID_ENTITY")

    workflow_request = get_workflow_request(db, ai_result.entities.request_id)
    return WorkflowResult(
        intent=AIIntent.REQUEST_STATUS,
        success=True,
        status=workflow_request.status.value,
        workflow_status=workflow_request.status,
        message="Workflow request status found.",
        request_id=workflow_request.id,
        request_type=workflow_request.request_type,
        priority=workflow_request.priority,
    )
