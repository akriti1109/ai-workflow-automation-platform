from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models import (  # noqa: E402,F401
    conversation,
    knowledge_chunk,
    knowledge_document,
    user,
    workflow_execution,
    workflow_request,
)
