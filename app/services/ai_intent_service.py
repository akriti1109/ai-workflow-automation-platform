from pydantic import ValidationError

from app.ai.providers import LLMProvider, LLMProviderError, LLMProviderTimeout
from app.core.errors import AppError
from app.schemas.ai import AIIntentResult


def interpret_user_request(text: str, provider: LLMProvider) -> AIIntentResult:
    try:
        provider_response = provider.extract_intent(text)
    except LLMProviderTimeout as exc:
        raise AppError(
            "AI provider timed out.",
            status_code=503,
            error_code="AI_PROVIDER_TIMEOUT",
        ) from exc
    except LLMProviderError as exc:
        raise AppError(
            "AI provider could not interpret the request.",
            status_code=503,
            error_code="AI_PROVIDER_ERROR",
        ) from exc

    try:
        return AIIntentResult.model_validate(provider_response)
    except ValidationError as exc:
        raise AppError(
            "AI provider returned an invalid interpretation.",
            status_code=502,
            error_code="INVALID_AI_RESPONSE",
        ) from exc

