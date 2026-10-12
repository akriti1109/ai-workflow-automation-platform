import pytest

from app.ai.providers import LLMProviderError, LLMProviderTimeout
from app.core.errors import AppError
from app.models.enums import RequestPriority
from app.schemas.ai import (
    AIIntent,
    AccessRequestEntities,
    KnowledgeQueryEntities,
    RequestStatusEntities,
    SupportRequestEntities,
    UnknownEntities,
)
from app.services.ai_intent_service import interpret_user_request


class FakeProvider:
    def __init__(
        self,
        response: dict[str, object] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or {}
        self.error = error

    def extract_intent(self, text: str) -> dict[str, object]:
        if self.error is not None:
            raise self.error
        return self.response


def test_access_request_classification() -> None:
    result = interpret_user_request(
        "I need access to the finance application.",
        FakeProvider(
            {
                "intent": "access_request",
                "priority": "medium",
                "entities": {"application": "finance"},
            }
        ),
    )

    assert result.intent is AIIntent.ACCESS_REQUEST
    assert result.priority is RequestPriority.MEDIUM
    assert isinstance(result.entities, AccessRequestEntities)
    assert result.entities.application == "finance"


def test_support_request_classification() -> None:
    result = interpret_user_request(
        "My laptop keeps disconnecting from Wi-Fi.",
        FakeProvider(
            {
                "intent": "support_request",
                "priority": "medium",
                "entities": {
                    "issue": "Laptop disconnecting from Wi-Fi",
                    "device": "laptop",
                },
            }
        ),
    )

    assert result.intent is AIIntent.SUPPORT_REQUEST
    assert isinstance(result.entities, SupportRequestEntities)
    assert result.entities.device == "laptop"


def test_knowledge_query_classification() -> None:
    result = interpret_user_request(
        "How do I reset my password?",
        FakeProvider(
            {
                "intent": "knowledge_query",
                "priority": "low",
                "entities": {"question": "How do I reset my password?"},
            }
        ),
    )

    assert result.intent is AIIntent.KNOWLEDGE_QUERY
    assert isinstance(result.entities, KnowledgeQueryEntities)
    assert result.entities.question == "How do I reset my password?"


def test_request_status_classification() -> None:
    result = interpret_user_request(
        "What is the status of request 25?",
        FakeProvider(
            {
                "intent": "request_status",
                "priority": "medium",
                "entities": {"request_id": 25},
            }
        ),
    )

    assert result.intent is AIIntent.REQUEST_STATUS
    assert isinstance(result.entities, RequestStatusEntities)
    assert result.entities.request_id == 25


def test_unknown_intent() -> None:
    result = interpret_user_request(
        "Please do the thing.",
        FakeProvider(
            {
                "intent": "unknown",
                "priority": "medium",
                "entities": {"reason": "Intent is unclear"},
            }
        ),
    )

    assert result.intent is AIIntent.UNKNOWN
    assert isinstance(result.entities, UnknownEntities)


def test_malformed_provider_response() -> None:
    with pytest.raises(AppError) as exc_info:
        interpret_user_request("Hello", FakeProvider({"intent": "access_request"}))

    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"
    assert exc_info.value.status_code == 502


def test_unsupported_intent_returned_by_provider() -> None:
    with pytest.raises(AppError) as exc_info:
        interpret_user_request(
            "Hello",
            FakeProvider(
                {
                    "intent": "delete_database",
                    "priority": "medium",
                    "entities": {},
                }
            ),
        )

    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"


def test_invalid_priority_returned_by_provider() -> None:
    with pytest.raises(AppError) as exc_info:
        interpret_user_request(
            "Hello",
            FakeProvider(
                {
                    "intent": "unknown",
                    "priority": "normal",
                    "entities": {"reason": "unclear"},
                }
            ),
        )

    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"


def test_provider_timeout() -> None:
    with pytest.raises(AppError) as exc_info:
        interpret_user_request(
            "Hello",
            FakeProvider(error=LLMProviderTimeout("timeout")),
        )

    assert exc_info.value.error_code == "AI_PROVIDER_TIMEOUT"
    assert exc_info.value.status_code == 503


def test_provider_failure() -> None:
    with pytest.raises(AppError) as exc_info:
        interpret_user_request(
            "Hello",
            FakeProvider(error=LLMProviderError("failure")),
        )

    assert exc_info.value.error_code == "AI_PROVIDER_ERROR"
    assert exc_info.value.status_code == 503


def test_correct_entity_validation() -> None:
    with pytest.raises(AppError) as exc_info:
        interpret_user_request(
            "What is the status of request?",
            FakeProvider(
                {
                    "intent": "request_status",
                    "priority": "medium",
                    "entities": {"request_id": "not-a-number"},
                }
            ),
        )

    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"

