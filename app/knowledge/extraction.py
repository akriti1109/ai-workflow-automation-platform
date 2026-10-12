from io import BytesIO
from pathlib import PurePath

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import AppError

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
ALLOWED_CONTENT_TYPES = {"application/pdf", "text/plain"}


def sanitize_filename(filename: str) -> str:
    safe_name = PurePath(filename).name.strip()
    if not safe_name:
        raise AppError("Invalid filename.", 400, "INVALID_FILENAME")
    return safe_name[:255]


def validate_document_file(
    filename: str,
    content_type: str,
    content: bytes,
    max_size_bytes: int,
) -> str:
    safe_name = sanitize_filename(filename)
    extension = PurePath(safe_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise AppError("Unsupported file extension.", 400, "UNSUPPORTED_FILE_TYPE")
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise AppError("Unsupported content type.", 400, "UNSUPPORTED_CONTENT_TYPE")
    if not content:
        raise AppError("Uploaded file is empty.", 400, "EMPTY_FILE")
    if len(content) > max_size_bytes:
        raise AppError("Uploaded file is too large.", 413, "FILE_TOO_LARGE")
    if extension == ".pdf" and content_type != "application/pdf":
        raise AppError("Unsupported content type.", 400, "UNSUPPORTED_CONTENT_TYPE")
    if extension == ".txt" and content_type != "text/plain":
        raise AppError("Unsupported content type.", 400, "UNSUPPORTED_CONTENT_TYPE")

    return safe_name


def extract_text(filename: str, content_type: str, content: bytes) -> str:
    extension = PurePath(filename).suffix.lower()
    if extension == ".txt" and content_type == "text/plain":
        return _extract_txt(content)
    if extension == ".pdf" and content_type == "application/pdf":
        return _extract_pdf(content)
    raise AppError("Unsupported document type.", 400, "UNSUPPORTED_FILE_TYPE")


def _extract_txt(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AppError("Text file could not be decoded.", 400, "MALFORMED_DOCUMENT") from exc
    return _require_useful_text(text)


def _extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise AppError("Encrypted PDFs are not supported.", 400, "MALFORMED_DOCUMENT")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except (PdfReadError, AppError) as exc:
        if isinstance(exc, AppError):
            raise
        raise AppError("PDF could not be read.", 400, "MALFORMED_DOCUMENT") from exc
    except Exception as exc:
        raise AppError("PDF could not be read.", 400, "MALFORMED_DOCUMENT") from exc
    return _require_useful_text(text)


def _require_useful_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise AppError("No useful text could be extracted.", 400, "NO_EXTRACTED_TEXT")
    return cleaned

