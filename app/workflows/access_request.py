from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import RequestType
from app.schemas.ai import AIIntent, AIIntentResult, AccessRequestEntities
from app.schemas.workflow import WorkflowResult
from app.workflows.execution import create_request_with_execution
from app.workflows.context import WorkflowContext


def handle_access_request(
    db: Session,
    user_id: int,
    original_request: str,
    ai_result: AIIntentResult,
    context: WorkflowContext,
) -> WorkflowResult:
    if not isinstance(ai_result.entities, AccessRequestEntities):
        raise AppError("Invalid access request entities.", 400, "INVALID_ENTITY")
    if not ai_result.entities.application:
        raise AppError(
            "Access request requires an application.",
            400,
            "MISSING_REQUIRED_ENTITY",
        )

    workflow_request = create_request_with_execution(
        db=db,
        user_id=user_id,
        request_type=RequestType.ACCESS_REQUEST,
        original_request=original_request,
        priority=ai_result.priority,
        action="create_access_request",
        result={"application": ai_result.entities.application},
        error_message="Unable to execute access request workflow.",
    )

    return WorkflowResult(
        intent=AIIntent.ACCESS_REQUEST,
        success=True,
        status=workflow_request.status.value,
        workflow_status=workflow_request.status,
        message="Access request created.",
        request_id=workflow_request.id,
        request_type=workflow_request.request_type,
        priority=workflow_request.priority,
    )
