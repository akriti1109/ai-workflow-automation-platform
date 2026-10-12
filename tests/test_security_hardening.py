from io import BytesIO

import pytest
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from app.api.knowledge import read_upload_file
from app.core.config import Settings
from app.core.errors import AppError


def build_settings(**overrides: object) -> Settings:
    values = {
        "database_url": "postgresql+psycopg://user:password@localhost:5432/db",
    }
    values.update(overrides)
    return Settings(**values)


def test_invalid_chunk_overlap_config_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_settings(rag_chunk_size=100, rag_chunk_overlap=100)


def test_unsafe_large_top_k_config_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_settings(rag_top_k=1000)


def test_unsafe_large_upload_limit_config_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_settings(rag_max_file_size_bytes=99_999_999)


def test_wildcard_cors_disables_credentials() -> None:
    settings = build_settings(cors_origins="*")

    assert settings.cors_origin_list == ["*"]
    assert settings.cors_allows_credentials is False


@pytest.mark.anyio
async def test_upload_read_rejects_oversized_file_before_ingestion() -> None:
    upload = UploadFile(filename="large.txt", file=BytesIO(b"abcdef"))

    with pytest.raises(AppError) as exc_info:
        await read_upload_file(upload, max_size_bytes=3)

    assert exc_info.value.status_code == 413
    assert exc_info.value.error_code == "FILE_TOO_LARGE"

