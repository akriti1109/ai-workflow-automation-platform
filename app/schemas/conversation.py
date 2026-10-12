from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ConversationRole


class ConversationCreate(BaseModel):
    user_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=5000)
    role: ConversationRole


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    message: str
    role: ConversationRole
    created_at: datetime

