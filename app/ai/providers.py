import json
import logging
from typing import Protocol

import httpx

from app.ai.prompts import INTENT_EXTRACTION_PROMPT
from app.core.config import Settings

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    pass


class LLMProviderTimeout(LLMProviderError):
    pass


class LLMProvider(Protocol):
    def extract_intent(self, text: str) -> dict[str, object]:
        pass

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        pass


class OpenAIResponsesProvider:
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.api_url = settings.llm_api_url
        self.timeout = settings.llm_timeout_seconds

    def extract_intent(self, text: str) -> dict[str, object]:
        self._validate_config()

        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=self._build_payload(text),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderTimeout("LLM provider timed out.") from exc
        except httpx.HTTPError as exc:
            logger.warning("LLM provider request failed")
            raise LLMProviderError("LLM provider request failed.") from exc

        output_text = self._extract_output_text(response.json())
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise LLMProviderError("LLM provider returned malformed JSON.") from exc

        if not isinstance(parsed, dict):
            raise LLMProviderError("LLM provider returned an invalid payload.")
        return parsed

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        self._validate_config()

        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LLMProviderTimeout("LLM provider timed out.") from exc
        except httpx.HTTPError as exc:
            logger.warning("LLM provider request failed")
            raise LLMProviderError("LLM provider request failed.") from exc

        return self._extract_output_text(response.json())

    def _validate_config(self) -> None:
        if not self.api_key or not self.model or not self.api_url:
            raise LLMProviderError("LLM provider is not configured.")

    def _build_payload(self, text: str) -> dict[str, object]:
        return {
            "model": self.model,
            "input": [
                {"role": "system", "content": INTENT_EXTRACTION_PROMPT},
                {"role": "user", "content": text},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "intent_extraction_result",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["intent", "priority", "entities"],
                        "properties": {
                            "intent": {
                                "type": "string",
                                "enum": [
                                    "access_request",
                                    "support_request",
                                    "knowledge_query",
                                    "request_status",
                                    "unknown",
                                ],
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high", "urgent"],
                            },
                            "entities": {"type": "object"},
                        },
                    },
                }
            },
        }

    def _extract_output_text(self, payload: dict[str, object]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str):
            return output_text

        output = payload.get("output")
        if not isinstance(output, list):
            raise LLMProviderError("LLM provider response did not include output.")

        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                text = content_item.get("text")
                if isinstance(text, str):
                    return text

        raise LLMProviderError("LLM provider response did not include text output.")
