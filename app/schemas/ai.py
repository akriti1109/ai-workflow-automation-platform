from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.models.enums import RequestPriority


class AIIntent(StrEnum):
    ACCESS_REQUEST = "access_request"
    SUPPORT_REQUEST = "support_request"
    KNOWLEDGE_QUERY = "knowledge_query"
    REQUEST_STATUS = "request_status"
    UNKNOWN = "unknown"


class AccessRequestEntities(BaseModel):
    application: str | None = Field(default=None, max_length=100)
    access_level: str | None = Field(default=None, max_length=100)


class SupportRequestEntities(BaseModel):
    issue: str | None = Field(default=None, max_length=500)
    device: str | None = Field(default=None, max_length=100)


class KnowledgeQueryEntities(BaseModel):
    topic: str | None = Field(default=None, max_length=200)
    question: str | None = Field(default=None, max_length=1000)


class RequestStatusEntities(BaseModel):
    request_id: int = Field(gt=0)


class UnknownEntities(BaseModel):
    reason: str | None = Field(default=None, max_length=300)


AIEntities = (
    AccessRequestEntities
    | SupportRequestEntities
    | KnowledgeQueryEntities
    | RequestStatusEntities
    | UnknownEntities
)


class AIInterpretRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class AIIntentResult(BaseModel):
    intent: AIIntent
    priority: RequestPriority = RequestPriority.MEDIUM
    entities: AIEntities

    @model_validator(mode="before")
    @classmethod
    def parse_entities_for_intent(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        intent = data.get("intent")
        entities = data.get("entities")
        if not isinstance(entities, dict):
            return data

        entity_models = {
            AIIntent.ACCESS_REQUEST.value: AccessRequestEntities,
            AIIntent.SUPPORT_REQUEST.value: SupportRequestEntities,
            AIIntent.KNOWLEDGE_QUERY.value: KnowledgeQueryEntities,
            AIIntent.REQUEST_STATUS.value: RequestStatusEntities,
            AIIntent.UNKNOWN.value: UnknownEntities,
        }
        entity_model = entity_models.get(intent)
        if entity_model is None:
            return data

        return {**data, "entities": entity_model.model_validate(entities)}

    @model_validator(mode="after")
    def validate_entities_match_intent(self) -> "AIIntentResult":
        expected_entities = {
            AIIntent.ACCESS_REQUEST: AccessRequestEntities,
            AIIntent.SUPPORT_REQUEST: SupportRequestEntities,
            AIIntent.KNOWLEDGE_QUERY: KnowledgeQueryEntities,
            AIIntent.REQUEST_STATUS: RequestStatusEntities,
            AIIntent.UNKNOWN: UnknownEntities,
        }
        entity_type = expected_entities[self.intent]
        if not isinstance(self.entities, entity_type):
            raise ValueError("entities do not match intent")
        return self
