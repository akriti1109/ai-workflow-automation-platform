from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import RequestStatus, RequestType
from app.schemas.workflow_request import (
    WorkflowRequestCreate,
    WorkflowRequestList,
    WorkflowRequestRead,
    WorkflowRequestStatusUpdate,
)
from app.services.workflow_request_service import (
    create_workflow_request,
    get_workflow_request,
    list_workflow_requests,
    update_workflow_request_status,
)

router = APIRouter(prefix="/api/v1/requests", tags=["workflow requests"])


@router.post(
    "",
    response_model=WorkflowRequestRead,
    status_code=status.HTTP_201_CREATED,
)
def create_request(
    request_data: WorkflowRequestCreate,
    db: Session = Depends(get_db),
) -> WorkflowRequestRead:
    return create_workflow_request(db, request_data)


@router.get("", response_model=WorkflowRequestList)
def list_requests(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    request_type: RequestType | None = None,
    db: Session = Depends(get_db),
) -> WorkflowRequestList:
    items, total = list_workflow_requests(
        db=db,
        limit=limit,
        offset=offset,
        status=status_filter,
        request_type=request_type,
    )
    return WorkflowRequestList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{request_id}", response_model=WorkflowRequestRead)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
) -> WorkflowRequestRead:
    return get_workflow_request(db, request_id)


@router.patch("/{request_id}/status", response_model=WorkflowRequestRead)
def update_request_status(
    request_id: int,
    status_update: WorkflowRequestStatusUpdate,
    db: Session = Depends(get_db),
) -> WorkflowRequestRead:
    return update_workflow_request_status(db, request_id, status_update.status)

