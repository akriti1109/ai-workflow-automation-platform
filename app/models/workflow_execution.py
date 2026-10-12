from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import WorkflowExecutionStatus, enum_values
from app.models.timestamps import utc_now

if TYPE_CHECKING:
    from app.models.workflow_request import WorkflowRequest


class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    __table_args__ = (
        CheckConstraint(
            "length(trim(action)) > 0",
            name="ck_workflow_executions_action_not_blank",
        ),
        Index("ix_workflow_executions_request_status", "request_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("workflow_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[WorkflowExecutionStatus] = mapped_column(
        Enum(
            WorkflowExecutionStatus,
            name="workflow_execution_status",
            values_callable=enum_values,
        ),
        default=WorkflowExecutionStatus.PENDING,
        nullable=False,
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    request: Mapped["WorkflowRequest"] = relationship(back_populates="executions")
