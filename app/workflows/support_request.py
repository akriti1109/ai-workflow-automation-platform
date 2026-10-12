from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import RequestType
from app.schemas.ai import AIIntent, AIIntentResult, SupportRequestEntities
from app.schemas.workflow import WorkflowResult
from app.workflows.execution import create_request_with_execution
from app.workflows.context import WorkflowContext


def handle_support_request(
    db: Session,
    user_id: int,
    original_request: str,
    ai_result: AIIntentResult,
    context: WorkflowContext,
) -> WorkflowResult:
    if not isinstance(ai_result.entities, SupportRequestEntities):
        raise AppError("Invalid support request entities.", 400, "INVALID_ENTITY")
    if not ai_result.entities.issue:
        raise AppError(
            "Support request requires an issue.",
            400,
            "MISSING_REQUIRED_ENTITY",
        )

    workflow_request = create_request_with_execution(
        db=db,
        user_id=user_id,
        request_type=RequestType.SUPPORT_REQUEST,
        original_request=original_request,
        priority=ai_result.priority,
        action="create_support_request",
        result={"issue": ai_result.entities.issue},
        error_message="Unable to execute support request workflow.",
    )

    return WorkflowResult(
        intent=AIIntent.SUPPORT_REQUEST,
        success=True,
        status=workflow_request.status.value,
        workflow_status=workflow_request.status,
        message="Support request created.",
        request_id=workflow_request.id,
        request_type=workflow_request.request_type,
        priority=workflow_request.priority,
    )
