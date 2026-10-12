import logging
from typing import Protocol

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingProviderError(Exception):
    pass


class EmbeddingProviderTimeout(EmbeddingProviderError):
    pass


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass


class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.llm_api_key
        self.model = settings.embedding_model
        self.api_url = settings.embedding_api_url
        self.timeout = settings.llm_timeout_seconds
        self.dimension = settings.embedding_dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._validate_config()
        if not texts:
            return []

        try:
            response = httpx.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model, "input": texts},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise EmbeddingProviderTimeout("Embedding provider timed out.") from exc
        except httpx.HTTPError as exc:
            logger.warning("Embedding provider request failed")
            raise EmbeddingProviderError("Embedding provider request failed.") from exc

        embeddings = self._parse_embeddings(response.json())
        if len(embeddings) != len(texts):
            raise EmbeddingProviderError("Embedding provider returned wrong count.")
        for embedding in embeddings:
            if len(embedding) != self.dimension:
                raise EmbeddingProviderError("Embedding provider returned wrong dimension.")
        return embeddings

    def _validate_config(self) -> None:
        if not self.api_key or not self.model or not self.api_url:
            raise EmbeddingProviderError("Embedding provider is not configured.")

    def _parse_embeddings(self, payload: dict[str, object]) -> list[list[float]]:
        data = payload.get("data")
        if not isinstance(data, list):
            raise EmbeddingProviderError("Embedding provider returned invalid data.")

        embeddings = []
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise EmbeddingProviderError("Embedding provider returned invalid embedding.")
            embeddings.append([float(value) for value in item["embedding"]])
        return embeddings

