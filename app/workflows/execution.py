import json

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import RequestPriority, RequestType, WorkflowExecutionStatus
from app.models.workflow_execution import WorkflowExecution
from app.models.workflow_request import WorkflowRequest
from app.schemas.workflow_request import WorkflowRequestCreate
from app.services.workflow_request_service import create_workflow_request


def record_execution(
    db: Session,
    request_id: int,
    action: str,
    status: WorkflowExecutionStatus,
    result: dict[str, object],
) -> WorkflowExecution:
    execution = WorkflowExecution(
        request_id=request_id,
        action=action,
        status=status,
        result=json.dumps(result, sort_keys=True),
    )
    db.add(execution)
    db.flush()
    return execution


def create_request_with_execution(
    db: Session,
    user_id: int,
    request_type: RequestType,
    original_request: str,
    priority: RequestPriority,
    action: str,
    result: dict[str, object],
    error_message: str,
) -> WorkflowRequest:
    try:
        workflow_request = create_workflow_request(
            db,
            WorkflowRequestCreate(
                user_id=user_id,
                request_type=request_type,
                original_request=original_request,
                priority=priority,
            ),
            commit=False,
        )
        record_execution(
            db,
            workflow_request.id,
            action,
            WorkflowExecutionStatus.COMPLETED,
            result,
        )
        db.commit()
        db.refresh(workflow_request)
    except SQLAlchemyError as exc:
        db.rollback()
        raise AppError(error_message, 500, "DATABASE_ERROR") from exc

    return workflow_request
