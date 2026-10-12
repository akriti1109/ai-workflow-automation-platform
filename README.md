# AI Workflow Automation Platform

A portfolio backend project that accepts natural-language work requests, uses an LLM to extract structured intent, routes the request through an explicit workflow allowlist, and stores workflow activity in PostgreSQL.

The project also includes a small Retrieval-Augmented Generation knowledge base using PostgreSQL with pgvector for document chunk embeddings.

## Features

- FastAPI REST API
- Environment-based configuration with `.env`
- PostgreSQL database with SQLAlchemy ORM
- Alembic migrations
- Docker Compose local PostgreSQL with pgvector
- Structured AI intent extraction
- Explicit workflow router and approved handlers
- Workflow request creation and status lookup
- Workflow execution recording
- PDF/TXT knowledge document ingestion
- Text chunking and embedding storage
- pgvector similarity search
- Grounded knowledge answers with sources
- Safe error responses
- Security-focused upload validation and provider error handling
- Pytest test suite

## Supported Workflows

Natural-language execution is available through:

```http
POST /api/v1/workflows/execute
```

Supported AI intents:

- `access_request`
- `support_request`
- `request_status`
- `knowledge_query`
- `unknown`

Persisted workflow request types:

- `access_request`
- `support_request`
- `knowledge_query`

Supported workflow statuses:

- `pending`
- `processing`
- `completed`
- `failed`

## Tech Stack

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- Docker Compose
- httpx
- pypdf
- pytest

## Architecture

```text
Client
  -> FastAPI route
  -> Pydantic validation
  -> AI intent service
  -> LLM provider
  -> validated AIIntentResult
  -> explicit workflow router
  -> approved workflow handler
  -> service/database layer
  -> PostgreSQL
```

RAG flow:

```text
Document upload
  -> file validation
  -> text extraction
  -> chunking
  -> embedding provider
  -> PostgreSQL + pgvector

Question
  -> query embedding
  -> pgvector similarity search
  -> retrieved chunks
  -> LLM answer using retrieved context
  -> answer + sources
```

The LLM does not execute workflows directly. It only returns structured data that is validated before the application chooses an approved handler.

## Local Setup

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

Create a local environment file:

```bash
cp .env.example .env
```

Update `.env` with local PostgreSQL and provider configuration.

## Environment Variables

`.env.example` contains placeholders only. Do not commit `.env`.

Required database settings:

```env
POSTGRES_DB=<database_name>
POSTGRES_USER=<database_user>
POSTGRES_PASSWORD=<database_password>
POSTGRES_HOST=<database_host>
POSTGRES_PORT=<database_port>
DATABASE_URL=postgresql+psycopg://<database_user>:<database_password>@<database_host>:<database_port>/<database_name>
```

LLM settings:

```env
LLM_API_KEY=<llm_api_key>
LLM_MODEL=<llm_model>
LLM_API_URL=<llm_api_url>
LLM_TIMEOUT_SECONDS=10
```

Embedding/RAG settings:

```env
EMBEDDING_MODEL=<embedding_model>
EMBEDDING_API_URL=<embedding_api_url>
EMBEDDING_DIMENSION=1536
RAG_MAX_FILE_SIZE_BYTES=1048576
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_TOP_K=3
```

## Local PostgreSQL

Start PostgreSQL with pgvector:

```bash
docker compose up -d postgres
```

Check status:

```bash
docker compose ps postgres
```

Stop PostgreSQL without deleting data:

```bash
docker compose down
```

## Database Migrations

Run migrations:

```bash
alembic upgrade head
```

Check migration state:

```bash
alembic heads
alembic current
```

Expected current head:

```text
20261004_0003
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## API Overview

Health:

```http
GET /health
```

Workflow requests:

```http
POST  /api/v1/requests
GET   /api/v1/requests
GET   /api/v1/requests/{request_id}
PATCH /api/v1/requests/{request_id}/status
```

AI interpretation:

```http
POST /api/v1/ai/interpret
```

Workflow execution:

```http
POST /api/v1/workflows/execute
```

Knowledge base:

```http
POST /api/v1/knowledge/documents
GET  /api/v1/knowledge/documents
POST /api/v1/knowledge/query
```

Example workflow execution request:

```json
{
  "user_id": 1,
  "text": "I need access to the finance application."
}
```

Example knowledge query request:

```json
{
  "question": "How should an employee request access to the Finance Portal?"
}
```

## Testing

Run the complete test suite:

```bash
pytest
```

The tests use fake LLM and embedding providers. They do not call real paid provider APIs.

## Security Notes

- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- API keys and database credentials are loaded from environment variables.
- Uploaded files are treated as untrusted input.
- Only PDF and TXT uploads are supported.
- File size, extension, MIME type, and text extraction are validated.
- LLM output is validated with Pydantic before use.
- Workflow routing uses an explicit allowlist.
- Retrieved document text is treated as data, not instructions.

## Known Limitations

- Authentication is intentionally not implemented yet.
- No frontend is included.
- No background workers are used.
- OCR and DOCX ingestion are not supported.
- Real LLM and embedding calls require valid provider configuration in `.env`.
