from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.knowledge.constants import DEFAULT_EMBEDDING_DIMENSION


class Settings(BaseSettings):
    app_name: str = "AI Workflow Automation Platform"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = Field(..., min_length=1)
    cors_origins: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_api_url: str = ""
    llm_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    embedding_model: str = ""
    embedding_api_url: str = ""
    embedding_dimension: int = Field(
        default=DEFAULT_EMBEDDING_DIMENSION,
        gt=0,
        le=8192,
    )
    rag_max_file_size_bytes: int = Field(default=1_048_576, gt=0, le=10_485_760)
    rag_chunk_size: int = Field(default=1000, gt=0, le=10_000)
    rag_chunk_overlap: int = Field(default=200, ge=0)
    rag_top_k: int = Field(default=3, gt=0, le=20)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_rag_config(self) -> "Settings":
        if self.rag_chunk_overlap >= self.rag_chunk_size:
            raise ValueError("RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE")
        return self

    @property
    def cors_allows_credentials(self) -> bool:
        return "*" not in self.cors_origin_list


@lru_cache
def get_settings() -> Settings:
    return Settings()
