from enum import StrEnum


def enum_values(enum_class: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_class]


class ConversationRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class RequestPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class RequestStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_INFO = "needs_info"


class RequestType(StrEnum):
    ACCESS_REQUEST = "access_request"
    SUPPORT_REQUEST = "support_request"
    STATUS_LOOKUP = "status_lookup"
    KNOWLEDGE_QUERY = "knowledge_query"


class WorkflowExecutionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
