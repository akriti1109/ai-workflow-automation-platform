from collections.abc import Callable

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.schemas.ai import AIIntent, AIIntentResult
from app.schemas.workflow import WorkflowResult
from app.workflows.access_request import handle_access_request
from app.workflows.knowledge_query import handle_knowledge_query
from app.workflows.request_status import handle_request_status
from app.workflows.support_request import handle_support_request
from app.workflows.unknown import handle_unknown
from app.workflows.context import WorkflowContext

WorkflowHandler = Callable[
    [Session, int, str, AIIntentResult, WorkflowContext],
    WorkflowResult,
]

WORKFLOW_HANDLERS: dict[AIIntent, WorkflowHandler] = {
    AIIntent.ACCESS_REQUEST: handle_access_request,
    AIIntent.SUPPORT_REQUEST: handle_support_request,
    AIIntent.REQUEST_STATUS: handle_request_status,
    AIIntent.KNOWLEDGE_QUERY: handle_knowledge_query,
    AIIntent.UNKNOWN: handle_unknown,
}


def route_workflow(
    db: Session,
    user_id: int,
    original_request: str,
    ai_result: AIIntentResult,
    context: WorkflowContext,
) -> WorkflowResult:
    handler = get_workflow_handler(ai_result.intent)
    return handler(db, user_id, original_request, ai_result, context)


def get_workflow_handler(intent: AIIntent) -> WorkflowHandler:
    handler = WORKFLOW_HANDLERS.get(intent)
    if handler is None:
        raise AppError(
            "No workflow handler is registered for this intent.",
            400,
            "UNSUPPORTED_WORKFLOW_INTENT",
        )
    return handler
