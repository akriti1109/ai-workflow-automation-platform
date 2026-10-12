from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import WorkflowExecutionStatus


class WorkflowExecutionCreate(BaseModel):
    request_id: int = Field(gt=0)
    action: str = Field(min_length=1, max_length=100)
    status: WorkflowExecutionStatus = WorkflowExecutionStatus.PENDING
    result: str | None = Field(default=None, max_length=10000)


class WorkflowExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    action: str
    status: WorkflowExecutionStatus
    result: str | None
    created_at: datetime

