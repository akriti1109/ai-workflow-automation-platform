from fastapi import APIRouter, Depends

from app.ai.providers import LLMProvider, OpenAIResponsesProvider
from app.core.config import get_settings
from app.schemas.ai import AIIntentResult, AIInterpretRequest
from app.services.ai_intent_service import interpret_user_request

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


def get_llm_provider() -> LLMProvider:
    return OpenAIResponsesProvider(get_settings())


@router.post("/interpret", response_model=AIIntentResult)
def interpret_request(
    request: AIInterpretRequest,
    provider: LLMProvider = Depends(get_llm_provider),
) -> AIIntentResult:
    return interpret_user_request(request.text, provider)

