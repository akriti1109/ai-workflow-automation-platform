import httpx
import pytest

from app.ai.providers import LLMProviderError, OpenAIResponsesProvider
from app.core.config import Settings


def build_settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://user:password@localhost:5432/db",
        llm_api_key="test-key",
        llm_model="test-model",
        llm_api_url="https://example.test/v1/responses",
        llm_timeout_seconds=1,
    )


def test_provider_rejects_malformed_json_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"output_text": "{not-json"},
            request=httpx.Request("POST", "https://example.test/v1/responses"),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAIResponsesProvider(build_settings())

    with pytest.raises(LLMProviderError):
        provider.extract_intent("I need access.")

