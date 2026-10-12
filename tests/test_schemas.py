import pytest
from pydantic import ValidationError

from app.models.enums import (
    ConversationRole,
    RequestPriority,
    RequestType,
    WorkflowExecutionStatus,
)
from app.schemas.conversation import ConversationCreate
from app.schemas.user import UserCreate
from app.schemas.workflow_execution import WorkflowExecutionCreate
from app.schemas.workflow_request import WorkflowRequestCreate


def test_user_create_requires_valid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreate(name="Akriti Sharma", email="not-an-email")


def test_workflow_request_create_uses_enum_values() -> None:
    schema = WorkflowRequestCreate(
        user_id=1,
        request_type="access_request",
        original_request="Please give me access to Salesforce.",
        priority="high",
    )

    assert schema.request_type is RequestType.ACCESS_REQUEST
    assert schema.priority is RequestPriority.HIGH


def test_workflow_request_create_rejects_unknown_request_type() -> None:
    with pytest.raises(ValidationError):
        WorkflowRequestCreate(
            user_id=1,
            request_type="unknown",
            original_request="Please check this request.",
        )


def test_workflow_execution_create_defaults_to_pending() -> None:
    schema = WorkflowExecutionCreate(request_id=1, action="create_ticket")

    assert schema.status is WorkflowExecutionStatus.PENDING


def test_conversation_create_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        ConversationCreate(user_id=1, message="Hello", role="admin")


def test_conversation_create_accepts_supported_role() -> None:
    schema = ConversationCreate(
        user_id=1,
        message="Hello",
        role="user",
    )

    assert schema.role is ConversationRole.USER

