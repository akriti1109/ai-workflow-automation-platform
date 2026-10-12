from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RequestPriority, RequestStatus, RequestType


SUPPORTED_REQUEST_TYPES = {
    RequestType.ACCESS_REQUEST,
    RequestType.SUPPORT_REQUEST,
    RequestType.KNOWLEDGE_QUERY,
}

SUPPORTED_REQUEST_STATUSES = {
    RequestStatus.PENDING,
    RequestStatus.PROCESSING,
    RequestStatus.COMPLETED,
    RequestStatus.FAILED,
}


class WorkflowRequestCreate(BaseModel):
    user_id: int = Field(gt=0)
    request_type: RequestType
    original_request: str = Field(min_length=1, max_length=5000)
    priority: RequestPriority = RequestPriority.MEDIUM


class WorkflowRequestStatusUpdate(BaseModel):
    status: RequestStatus


class WorkflowRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    request_type: RequestType
    original_request: str
    status: RequestStatus
    priority: RequestPriority
    created_at: datetime
    updated_at: datetime


class WorkflowRequestList(BaseModel):
    items: list[WorkflowRequestRead]
    total: int
    limit: int
    offset: int
