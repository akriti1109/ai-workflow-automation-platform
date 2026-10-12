import logging

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.enums import RequestStatus, RequestType
from app.models.user import User
from app.models.workflow_request import WorkflowRequest
from app.schemas.workflow_request import (
    SUPPORTED_REQUEST_STATUSES,
    SUPPORTED_REQUEST_TYPES,
    WorkflowRequestCreate,
)

logger = logging.getLogger(__name__)

VALID_STATUS_TRANSITIONS = {
    RequestStatus.PENDING: {RequestStatus.PROCESSING, RequestStatus.FAILED},
    RequestStatus.PROCESSING: {RequestStatus.COMPLETED, RequestStatus.FAILED},
}


def create_workflow_request(
    db: Session,
    request_data: WorkflowRequestCreate,
    commit: bool = True,
) -> WorkflowRequest:
    _validate_supported_request_type(request_data.request_type)
    _get_user_or_raise(db, request_data.user_id)

    workflow_request = WorkflowRequest(
        user_id=request_data.user_id,
        request_type=request_data.request_type,
        original_request=request_data.original_request,
        priority=request_data.priority,
    )

    try:
        db.add(workflow_request)
        if commit:
            db.commit()
            db.refresh(workflow_request)
        else:
            db.flush()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to create workflow request")
        raise AppError(
            "Unable to create workflow request.",
            status_code=500,
            error_code="DATABASE_ERROR",
        ) from exc

    return workflow_request


def get_workflow_request(db: Session, request_id: int) -> WorkflowRequest:
    workflow_request = db.get(WorkflowRequest, request_id)
    if workflow_request is None:
        raise AppError(
            "Workflow request not found.",
            status_code=404,
            error_code="WORKFLOW_REQUEST_NOT_FOUND",
        )
    return workflow_request


def list_workflow_requests(
    db: Session,
    limit: int,
    offset: int,
    status: RequestStatus | None = None,
    request_type: RequestType | None = None,
) -> tuple[list[WorkflowRequest], int]:
    if status is not None:
        _validate_supported_status(status)
    if request_type is not None:
        _validate_supported_request_type(request_type)

    filters = []
    if status is not None:
        filters.append(WorkflowRequest.status == status)
    if request_type is not None:
        filters.append(WorkflowRequest.request_type == request_type)

    query = select(WorkflowRequest).order_by(WorkflowRequest.created_at.desc())
    count_query = select(func.count()).select_from(WorkflowRequest)

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    items = db.scalars(query.offset(offset).limit(limit)).all()
    total = db.scalar(count_query) or 0
    return list(items), total


def update_workflow_request_status(
    db: Session,
    request_id: int,
    new_status: RequestStatus,
) -> WorkflowRequest:
    _validate_supported_status(new_status)
    workflow_request = get_workflow_request(db, request_id)

    if not _is_valid_status_transition(workflow_request.status, new_status):
        raise AppError(
            "Invalid workflow request status transition.",
            status_code=400,
            error_code="INVALID_STATUS_TRANSITION",
        )

    workflow_request.status = new_status

    try:
        db.commit()
        db.refresh(workflow_request)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to update workflow request status")
        raise AppError(
            "Unable to update workflow request status.",
            status_code=500,
            error_code="DATABASE_ERROR",
        ) from exc

    return workflow_request


def _get_user_or_raise(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppError(
            "User not found.",
            status_code=404,
            error_code="USER_NOT_FOUND",
        )
    return user


def _validate_supported_request_type(request_type: RequestType) -> None:
    if request_type not in SUPPORTED_REQUEST_TYPES:
        raise AppError(
            "Unsupported workflow request type.",
            status_code=400,
            error_code="UNSUPPORTED_REQUEST_TYPE",
        )


def _validate_supported_status(status: RequestStatus) -> None:
    if status not in SUPPORTED_REQUEST_STATUSES:
        raise AppError(
            "Unsupported workflow request status.",
            status_code=400,
            error_code="UNSUPPORTED_REQUEST_STATUS",
        )


def _is_valid_status_transition(
    current_status: RequestStatus,
    new_status: RequestStatus,
) -> bool:
    allowed_statuses = VALID_STATUS_TRANSITIONS.get(current_status, set())
    return new_status in allowed_statuses
