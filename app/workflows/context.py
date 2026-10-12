from dataclasses import dataclass

from app.ai.providers import LLMProvider
from app.core.config import Settings
from app.knowledge.embeddings import EmbeddingProvider


@dataclass(frozen=True)
class WorkflowContext:
    settings: Settings
    embedding_provider: EmbeddingProvider
    llm_provider: LLMProvider

