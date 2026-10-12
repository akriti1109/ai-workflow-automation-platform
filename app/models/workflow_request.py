from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RequestPriority, RequestStatus, RequestType, enum_values
from app.models.timestamps import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workflow_execution import WorkflowExecution


class WorkflowRequest(Base):
    __tablename__ = "workflow_requests"
    __table_args__ = (
        CheckConstraint(
            "length(trim(original_request)) > 0",
            name="ck_workflow_requests_original_request_not_blank",
        ),
        Index("ix_workflow_requests_user_status", "user_id", "status"),
        Index("ix_workflow_requests_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    request_type: Mapped[RequestType] = mapped_column(
        Enum(
            RequestType,
            name="request_type",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    original_request: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            name="request_status",
            values_callable=enum_values,
        ),
        default=RequestStatus.PENDING,
        nullable=False,
    )
    priority: Mapped[RequestPriority] = mapped_column(
        Enum(
            RequestPriority,
            name="request_priority",
            values_callable=enum_values,
        ),
        default=RequestPriority.MEDIUM,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="workflow_requests")
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
    )
