from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.timestamps import utc_now

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.workflow_request import WorkflowRequest


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    workflow_requests: Mapped[list["WorkflowRequest"]] = relationship(
        back_populates="user",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
    )
