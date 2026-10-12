from datetime import UTC

from app.db.base import Base
from app.models.conversation import Conversation
from app.models.enums import RequestPriority, RequestStatus, RequestType
from app.models.timestamps import utc_now
from app.models.user import User
from app.models.workflow_execution import WorkflowExecution
from app.models.workflow_request import WorkflowRequest


def test_metadata_contains_core_tables() -> None:
    assert {
        "users",
        "workflow_requests",
        "workflow_executions",
        "conversations",
    }.issubset(Base.metadata.tables)


def test_user_email_has_unique_constraint_and_index() -> None:
    email_column = User.__table__.columns["email"]

    assert email_column.unique is True
    assert email_column.index is True


def test_workflow_request_has_useful_indexes_and_constraints() -> None:
    index_names = {index.name for index in WorkflowRequest.__table__.indexes}
    constraint_names = {
        constraint.name
        for constraint in WorkflowRequest.__table__.constraints
        if constraint.name
    }

    assert "ix_workflow_requests_user_status" in index_names
    assert "ix_workflow_requests_created_at" in index_names
    assert "ck_workflow_requests_original_request_not_blank" in constraint_names


def test_child_tables_have_lookup_indexes() -> None:
    conversation_indexes = {index.name for index in Conversation.__table__.indexes}
    execution_indexes = {index.name for index in WorkflowExecution.__table__.indexes}

    assert "ix_conversations_user_created_at" in conversation_indexes
    assert "ix_workflow_executions_request_status" in execution_indexes


def test_relationships_are_configured() -> None:
    assert User.workflow_requests.property.back_populates == "user"
    assert User.conversations.property.back_populates == "user"
    assert WorkflowRequest.executions.property.back_populates == "request"
    assert WorkflowExecution.request.property.back_populates == "executions"
    assert Conversation.user.property.back_populates == "conversations"


def test_model_defaults_use_expected_enums() -> None:
    request = WorkflowRequest(
        user_id=1,
        request_type=RequestType.ACCESS_REQUEST,
        original_request="Need access.",
    )

    assert request.status is None
    assert request.priority is None

    status_default = WorkflowRequest.__table__.columns["status"].default.arg
    priority_default = WorkflowRequest.__table__.columns["priority"].default.arg

    assert status_default == RequestStatus.PENDING
    assert priority_default == RequestPriority.MEDIUM


def test_timestamp_columns_are_timezone_aware() -> None:
    assert User.__table__.columns["created_at"].type.timezone is True
    assert WorkflowRequest.__table__.columns["created_at"].type.timezone is True
    assert WorkflowRequest.__table__.columns["updated_at"].type.timezone is True
    assert WorkflowExecution.__table__.columns["created_at"].type.timezone is True
    assert Conversation.__table__.columns["created_at"].type.timezone is True


def test_utc_now_returns_timezone_aware_datetime() -> None:
    timestamp = utc_now()

    assert timestamp.tzinfo is UTC

