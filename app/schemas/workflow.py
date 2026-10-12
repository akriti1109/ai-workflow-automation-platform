from pydantic import BaseModel, Field

from app.models.enums import RequestPriority, RequestStatus, RequestType
from app.schemas.ai import AIIntent, AIInterpretRequest
from app.schemas.knowledge import KnowledgeSource


class WorkflowExecuteRequest(AIInterpretRequest):
    user_id: int = Field(gt=0)


class WorkflowResult(BaseModel):
    intent: AIIntent
    success: bool
    status: str
    message: str
    request_id: int | None = None
    request_type: RequestType | None = None
    priority: RequestPriority | None = None
    workflow_status: RequestStatus | None = None
    sources: list[KnowledgeSource] = Field(default_factory=list)
