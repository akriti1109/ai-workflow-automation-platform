"""create core workflow tables

Revision ID: 20261004_0001
Revises:
Create Date: 2026-10-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261004_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


conversation_role = postgresql.ENUM(
    "user",
    "assistant",
    "system",
    name="conversation_role",
    create_type=False,
)
request_priority = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "urgent",
    name="request_priority",
    create_type=False,
)
request_status = postgresql.ENUM(
    "pending",
    "in_progress",
    "completed",
    "failed",
    "needs_info",
    name="request_status",
    create_type=False,
)
request_type = postgresql.ENUM(
    "access_request",
    "support_request",
    "status_lookup",
    "knowledge_query",
    name="request_type",
    create_type=False,
)
workflow_execution_status = postgresql.ENUM(
    "pending",
    "completed",
    "failed",
    name="workflow_execution_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    conversation_role.create(bind, checkfirst=True)
    request_priority.create(bind, checkfirst=True)
    request_status.create(bind, checkfirst=True)
    request_type.create(bind, checkfirst=True)
    workflow_execution_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "workflow_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", request_type, nullable=False),
        sa.Column("original_request", sa.Text(), nullable=False),
        sa.Column(
            "status",
            request_status,
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "priority",
            request_priority,
            server_default="medium",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(original_request)) > 0",
            name="ck_workflow_requests_original_request_not_blank",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_requests_created_at",
        "workflow_requests",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_requests_user_status",
        "workflow_requests",
        ["user_id", "status"],
        unique=False,
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("role", conversation_role, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(message)) > 0",
            name="ck_conversations_message_not_blank",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversations_user_created_at",
        "conversations",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            workflow_execution_status,
            server_default="pending",
            nullable=False,
        ),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(trim(action)) > 0",
            name="ck_workflow_executions_action_not_blank",
        ),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["workflow_requests.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workflow_executions_request_status",
        "workflow_executions",
        ["request_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_executions_request_status",
        table_name="workflow_executions",
    )
    op.drop_table("workflow_executions")

    op.drop_index("ix_conversations_user_created_at", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_workflow_requests_user_status", table_name="workflow_requests")
    op.drop_index("ix_workflow_requests_created_at", table_name="workflow_requests")
    op.drop_table("workflow_requests")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    workflow_execution_status.drop(op.get_bind(), checkfirst=True)
    request_type.drop(op.get_bind(), checkfirst=True)
    request_status.drop(op.get_bind(), checkfirst=True)
    request_priority.drop(op.get_bind(), checkfirst=True)
    conversation_role.drop(op.get_bind(), checkfirst=True)
