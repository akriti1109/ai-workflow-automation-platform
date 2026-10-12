from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.ai.providers import LLMProviderError
from app.api.ai import get_llm_provider
from app.main import app


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


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_ai_interpret_endpoint_success(client: TestClient) -> None:
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(
        {
            "intent": "access_request",
            "priority": "medium",
            "entities": {"application": "finance"},
        }
    )

    response = client.post(
        "/api/v1/ai/interpret",
        json={"text": "I need access to the finance application."},
    )

    assert response.status_code == 200
    assert response.json() == {
        "intent": "access_request",
        "priority": "medium",
        "entities": {"application": "finance", "access_level": None},
    }


def test_ai_interpret_endpoint_failure_handling(client: TestClient) -> None:
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(
        error=LLMProviderError("provider failed")
    )

    response = client.post(
        "/api/v1/ai/interpret",
        json={"text": "I need help."},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_PROVIDER_ERROR"


def test_ai_interpret_endpoint_rejects_empty_input(client: TestClient) -> None:
    response = client.post("/api/v1/ai/interpret", json={"text": ""})

    assert response.status_code == 422


def test_ai_interpret_endpoint_rejects_oversized_input(client: TestClient) -> None:
    response = client.post("/api/v1/ai/interpret", json={"text": "x" * 1001})

    assert response.status_code == 422

