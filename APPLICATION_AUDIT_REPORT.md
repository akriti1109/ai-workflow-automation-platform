# AI Workflow Automation Platform - Application Audit Report

Audit date: 2026-10-12  
Repository: https://github.com/akriti1109/ai-workflow-automation-platform  
Scope: Source code, README, configuration, Docker Compose, Alembic migrations, SQLAlchemy models, FastAPI routes, AI/RAG services, workflow handlers, and tests.

## A. Executive Summary

The application is a clean, portfolio-suitable FastAPI backend for natural-language workflow intake, explicit workflow routing, request persistence, and a small PostgreSQL/pgvector-backed knowledge base. The implementation is materially stronger than a scaffold: it has typed settings, Pydantic validation, SQLAlchemy models, Alembic migrations, safe API errors, upload validation, mocked AI test coverage, and a documented local setup.

Final conclusion: **Conditionally Ready**.

It is ready for a local portfolio demo and code review, provided the evaluator understands that authentication is intentionally absent and real AI provider calls require environment configuration. It is **not production ready** for public or multi-user deployment until access control, rate limiting, real-provider verification, dependency security scanning, operational controls, and several reliability gaps are addressed.

Verification summary:

- `python -m pytest`: **92 passed, 1 warning**
- `python -m pip check`: **No broken requirements found**
- `alembic heads`: **20261004_0003 (head)**
- `uvicorn app.main:app --host 127.0.0.1 --port 8021` plus `GET /health`: **200 OK, {"status":"ok"}**
- `docker compose ps postgres`: **Blocked**, Docker daemon not running
- `alembic current`: **Blocked**, local PostgreSQL unavailable at `127.0.0.1:5433`
- `pip-audit`: **Unavailable**, not installed in the environment

## B. Verified Technology Stack

Supported by `pyproject.toml`, source imports, migrations, and tests:

- Python 3.12+
- FastAPI
- Pydantic and pydantic-settings
- SQLAlchemy ORM
- Alembic
- PostgreSQL
- pgvector
- Docker Compose for local PostgreSQL
- httpx for provider calls
- pypdf for PDF extraction
- pytest

Evidence:

- Dependencies are declared in `pyproject.toml:7-19`.
- Package discovery is constrained to `app*` in `pyproject.toml:30-31`, avoiding the earlier setuptools flat-layout issue.
- Docker Compose uses `pgvector/pgvector:pg16` and binds PostgreSQL to localhost in `docker-compose.yml:3` and `docker-compose.yml:10-11`.

## C. Requirements Traceability Matrix

| Requirement | Expected behavior | Implementation evidence | Test evidence | Status |
|---|---|---|---|---|
| FastAPI REST API | App exposes documented API routes | Routers included in `app/main.py:29-33`; endpoint docs in `README.md:222-257` | `tests/test_health.py`, `tests/test_requests_api.py`, `tests/test_ai_api.py`, `tests/test_knowledge.py`, `tests/test_workflow_execution.py` | Implemented |
| Environment-based config | No hardcoded secrets; settings from env | `Settings` in `app/core/config.py:9-58`; `.env.example` placeholders | `tests/test_security_hardening.py:20-39` | Implemented |
| PostgreSQL and SQLAlchemy | ORM models and session setup | `app/db/session.py:8-19`; models under `app/models` | Model/API tests use SQLAlchemy sessions | Implemented |
| Alembic migrations | Schema is migratable | `alembic/versions/20261004_0001...`, `_0002...`, `_0003...` | `alembic heads` verified head only; live current blocked | Partially Implemented |
| Health endpoint | Returns basic health status | `app/api/health.py`; router included in `app/main.py:29` | `tests/test_health.py`; live curl verified | Implemented |
| Workflow request APIs | Create, get, list, update status | `app/api/requests.py:22-66`; service in `app/services/workflow_request_service.py` | `tests/test_requests_api.py:75-234` | Implemented |
| Status transition validation | Only allowed transitions accepted | `VALID_STATUS_TRANSITIONS` in `app/services/workflow_request_service.py:19-22` | `tests/test_requests_api.py:195-224` | Implemented |
| Natural-language AI interpretation | LLM extracts structured intent | `app/ai/providers.py:36-64`; schema validation in `app/services/ai_intent_service.py:8-31` | Mocked tests in `tests/test_ai_intent_service.py` and `tests/test_llm_provider.py` | Partially Implemented |
| Explicit workflow allowlist | LLM cannot directly execute arbitrary workflows | `WORKFLOW_HANDLERS` in `app/workflows/router.py:20-26` | `tests/test_workflow_execution.py:335-345` | Implemented |
| Access request workflow | Create workflow request and execution | `app/workflows/access_request.py:11-47` | `tests/test_workflow_execution.py:118-138` | Implemented |
| Support request workflow | Create workflow request and execution | `app/workflows/support_request.py:11-47` | `tests/test_workflow_execution.py:139-156` | Implemented |
| Request status lookup | Return existing request status | `app/workflows/request_status.py:10-30` | `tests/test_workflow_execution.py:158-196` | Implemented |
| Knowledge query | Answer from RAG context | `app/workflows/knowledge_query.py:10-34`; `app/services/knowledge_service.py` | `tests/test_knowledge.py:271-382` | Partially Implemented |
| Document ingestion | Accept PDF/TXT, validate, chunk, embed, store | `app/api/knowledge.py:30-49`; `app/services/document_ingestion_service.py:22-119` | `tests/test_knowledge.py:132-238` | Implemented |
| Safe upload handling | Validate extension, MIME, size, text extraction | `app/knowledge/extraction.py:9-81`; bounded read in `app/api/knowledge.py:52-67` | `tests/test_security_hardening.py:42-50`; `tests/test_knowledge.py:132-169` | Implemented |
| Safe API error responses | No stack traces in client responses | `app/core/errors.py:21-53` | Error tests across suite | Implemented |
| Secret hygiene | `.env` ignored, placeholders only | `.gitignore:1-3`; `.env.example`; README security notes | `git check-ignore` verified `.env`, `.venv`, cache, egg-info | Implemented |
| Real LLM/embedding E2E | Verify provider integrations with real config | Provider code exists | Not run; README says tests use fakes in `README.md:284` | Unverified |
| Authentication/authorization | Protect users and objects if public/multi-user | README explicitly states missing in `README.md:300` | No tests | Missing by design |
| Background jobs/retries | Recover from long-running provider/document work | README limitation in `README.md:302`; no queue/retry code | No tests | Missing |

## D. Architecture Assessment

Rating: **Supported** for portfolio/local demo, **Partially Supported** for production.

Strengths:

- Simple and explainable route -> service -> SQLAlchemy architecture.
- FastAPI route handlers are small, for example `app/api/requests.py:27-31` delegates creation to a service.
- Workflow routing is explicit and allowlisted in `app/workflows/router.py:20-26`.
- Provider access is behind small protocols in `app/ai/providers.py:21-26` and `app/knowledge/embeddings.py:19-21`, which keeps tests simple without over-engineering.
- Configuration is centralized in `app/core/config.py`.

Concerns:

- Synchronous SQLAlchemy and blocking provider calls are used inside request handling. This is acceptable for the current portfolio scope, but it limits concurrency for document ingestion and AI workflows.
- `Conversation` is modeled but not used by an API or service. That is harmless, but it is a feature-completeness gap if conversation persistence is part of the intended story.
- There is no CI workflow, coverage reporting, formatter, or linter configuration.

No folder restructuring is required at this stage. The current structure is appropriate for the project size.

## E. Feature Completeness Assessment

Implemented:

- Health endpoint
- Workflow request CRUD/list/status API subset
- Access request workflow
- Support request workflow
- Request status lookup workflow
- AI interpretation endpoint
- Knowledge document upload/list/query
- SQLAlchemy models and migrations
- Local PostgreSQL Compose configuration
- Safe error response shape
- Test suite covering main behavior

Partially implemented or unverified:

- Real LLM and embedding integrations exist but were not verified with live provider credentials.
- Knowledge answers rely on prompt instruction for grounding but do not enforce a retrieval similarity threshold.
- Workflow execution records successful access/support workflow actions, but not all failed attempts, status lookups, or knowledge queries.
- Database migration current state could not be verified locally because Docker/PostgreSQL was unavailable during this audit.

Missing by current documented limitation:

- Authentication and authorization
- Frontend
- Background workers
- OCR and DOCX ingestion

## F. API and Database Findings

### API Findings

- Endpoints are consistent and use Pydantic schemas.
- Pagination bounds are present for listing endpoints, for example `limit` is constrained to `1..100` in `app/api/requests.py:36` and `app/api/knowledge.py:72`.
- Error responses are intentionally sanitized by `app/core/errors.py:31-53`.
- Provider failures are mapped to safe `503` responses in service code.

### Database Findings

- User email uniqueness and index are present in `app/models/user.py:20`.
- Workflow request checks and indexes are present in `app/models/workflow_request.py:18-25`.
- Workflow execution checks and indexes are present in `app/models/workflow_execution.py:17-23`.
- Knowledge chunks use `Vector(DEFAULT_EMBEDDING_DIMENSION)` in `app/models/knowledge_chunk.py:33-35`.
- pgvector extension and IVFFLAT index are created in `alembic/versions/20261004_0003_add_knowledge_documents.py:23-82`.

### Issue API-001

- Severity: Medium
- Affected file and line: `app/models/enums.py:21-34`; `app/schemas/workflow_request.py:8-19`
- Evidence: Database enums include `in_progress`, `needs_info`, and `status_lookup`, while schema/service allowlists only support `pending`, `processing`, `completed`, `failed`, and request types `access_request`, `support_request`, `knowledge_query`.
- Impact: Future developers may think legacy values are supported because they exist at the model/database enum level. It can also complicate API documentation and migration semantics.
- Recommended solution: Either remove unsupported enum values through a planned migration or explicitly document them as legacy/reserved values. Keep model enums aligned with public schemas where possible.
- Estimated implementation complexity: Medium, because PostgreSQL enum cleanup requires careful migration planning.

### Issue DB-001

- Severity: Low
- Affected file and line: `alembic/versions/20261004_0002_add_processing_request_status.py:23-25`
- Evidence: Downgrade is intentionally `pass` because PostgreSQL cannot safely drop enum values without type recreation.
- Impact: Rollbacks are incomplete for this migration.
- Recommended solution: Document this limitation in migration notes or implement a full enum type recreation downgrade if rollback support is required.
- Estimated implementation complexity: Medium.

### Issue DB-002

- Severity: Medium
- Affected file and line: `alembic/versions/20261004_0003_add_knowledge_documents.py:23-24`
- Evidence: Migration runs `CREATE EXTENSION IF NOT EXISTS vector`.
- Impact: Production databases may reject this if the application migration role lacks extension privileges or pgvector is not installed.
- Recommended solution: Document required database privileges and preinstall pgvector in production. Consider separating privileged extension setup from app-owned schema migrations.
- Estimated implementation complexity: Low to Medium.

## G. AI/RAG/Workflow Findings

Strengths:

- Intent extraction uses a strict JSON schema in `app/ai/providers.py:105-133`.
- AI output is validated against typed entities in `app/schemas/ai.py:52-93`.
- Prompt-injection mitigation exists in `app/ai/prompts.py:17-22`.
- Retrieved document content is delimited in `app/services/knowledge_service.py:95-106`.
- Workflow execution is allowlisted in `app/workflows/router.py:20-26`.

### Issue AI-001

- Severity: Medium
- Affected file and line: `app/ai/providers.py:39-54`; `app/knowledge/embeddings.py:37-52`
- Evidence: Provider calls have a timeout but no retry, backoff, or circuit-breaker behavior.
- Impact: Transient provider failures can fail user workflows immediately.
- Recommended solution: Add a small bounded retry policy for transient timeout/5xx errors, with backoff and clear logging. Avoid retrying validation/client errors.
- Estimated implementation complexity: Low.

### Issue RAG-001

- Severity: Medium
- Affected file and line: `app/services/knowledge_service.py:88-120`; `app/services/knowledge_service.py:133-157`
- Evidence: Retrieval returns the top K chunks whenever rows exist. There is no minimum similarity or maximum distance threshold before sending context to the LLM.
- Impact: Unrelated chunks may be treated as context, increasing hallucination or misleading answer risk.
- Recommended solution: Add a configurable relevance threshold and tests for unrelated questions. For PostgreSQL cosine distance, filter by a maximum distance. For the Python fallback, filter by minimum cosine similarity.
- Estimated implementation complexity: Low to Medium.

### Issue WF-001

- Severity: Low
- Affected file and line: `app/workflows/request_status.py:10-30`; `app/workflows/knowledge_query.py:10-34`; `app/workflows/execution.py:32-66`
- Evidence: Only access/support workflows create `WorkflowExecution` records. Status lookups and knowledge queries return results but do not create execution records.
- Impact: Workflow observability is incomplete.
- Recommended solution: Decide whether every workflow invocation should be auditable. If yes, record executions for status lookups, knowledge queries, unknown intents, and failed validations without storing sensitive full text.
- Estimated implementation complexity: Medium.

### Issue AI-002

- Severity: Medium
- Affected file and line: `README.md:284`; provider code in `app/ai/providers.py` and `app/knowledge/embeddings.py`
- Evidence: The README states tests use fake LLM and embedding providers. No live provider E2E test was run.
- Impact: The integration contract may drift from provider behavior.
- Recommended solution: Add optional, skipped-by-default integration tests that run only when explicit test provider environment variables are present.
- Estimated implementation complexity: Low.

## H. Security Vulnerabilities

### Issue SEC-001

- Severity: High
- Affected file and line: `app/api/requests.py:52-66`; `app/api/workflows.py:16-31`; `app/api/knowledge.py:70-94`
- Evidence: APIs accept or expose object identifiers without authentication, authorization, or object ownership checks. README confirms authentication is not implemented in `README.md:300`.
- Exploitability: High if deployed outside a trusted local/demo environment.
- Impact: Any caller can create requests for any `user_id`, list all requests, read request status by ID, upload/list/query knowledge documents, and infer workflow data.
- Recommended solution: Add authentication before public deployment. Then enforce object-level authorization for request IDs, user IDs, documents, and workflow execution.
- Estimated implementation complexity: Medium to High.

### Issue SEC-002

- Severity: Medium
- Affected file and line: `app/api/knowledge.py:52-67`; `app/knowledge/extraction.py:62-74`
- Evidence: Application-level upload reads are bounded, but document parsing and embedding generation still occur synchronously in the request path.
- Exploitability: Medium.
- Impact: Repeated uploads, malformed PDFs, or slow provider calls can consume request workers.
- Recommended solution: Add reverse-proxy/server body-size limits, per-client rate limiting, and move ingestion/embedding to a background job for non-demo deployment.
- Estimated implementation complexity: Medium.

### Issue SEC-003

- Severity: Medium
- Affected file and line: `app/ai/providers.py:31-34`; `app/knowledge/embeddings.py:26-30`
- Evidence: Provider URLs are loaded from environment variables and used for outbound requests.
- Exploitability: Low in normal deployment because environment variables are operator-controlled; higher if untrusted parties can influence runtime configuration.
- Impact: Misconfiguration could send prompts or document text to the wrong endpoint.
- Recommended solution: Document trusted provider URL requirements. Optionally validate provider URLs against allowed hosts in production settings.
- Estimated implementation complexity: Low.

### Issue SEC-004

- Severity: Medium
- Affected file and line: `pyproject.toml:7-24`
- Evidence: Dependencies use lower bounds only and no lock file is committed. `pip-audit` was unavailable, so known vulnerability scanning was not completed.
- Exploitability: Depends on future dependency resolution.
- Impact: Builds are less reproducible and may pull newly released vulnerable or incompatible versions.
- Recommended solution: Add a lock/constraints workflow and run dependency vulnerability scanning in CI.
- Estimated implementation complexity: Low.

Security positives:

- No real secrets were found in tracked files during pattern scanning; matches were placeholders, test fixtures, and source references.
- `.env` is ignored by `.gitignore:1-3`.
- CORS wildcard disables credentials through `app/core/config.py:51-53`.
- API errors avoid internal stack traces through `app/core/errors.py:45-53`.
- File upload validation checks extension, MIME type, empty content, size, encrypted/malformed PDFs, and useful extracted text.

## I. Test Results and Coverage

Executed commands:

```bash
.venv/bin/python -m pytest
```

Result:

```text
92 passed, 1 warning in 0.55s
```

Warning:

- Starlette/FastAPI TestClient deprecation warning related to `httpx`.

Additional checks:

```bash
.venv/bin/python -m pip check
```

Result:

```text
No broken requirements found.
```

```bash
.venv/bin/python -m alembic heads
```

Result:

```text
20261004_0003 (head)
```

```bash
curl -sS http://127.0.0.1:8021/health
```

Result:

```json
{"status":"ok"}
```

Coverage strengths:

- Request API creation/listing/filtering/pagination/status transitions.
- Workflow routing and workflow behavior.
- AI response validation and provider error mapping with fake providers.
- Document validation, extraction, chunking, ingestion rollback, RAG querying, upload hardening.
- Configuration hardening.
- Health endpoint.

Coverage gaps:

- No live PostgreSQL integration test was run during this audit because Docker was unavailable.
- No real LLM/embedding provider test was run.
- No authentication/security tests exist because authentication is absent.
- No dependency vulnerability scan completed because `pip-audit` was not installed.
- No coverage percentage was produced because coverage tooling is not configured.

## J. Performance and Reliability Findings

### Issue REL-001

- Severity: Medium
- Affected file and line: `app/api/knowledge.py:35-49`; `app/services/document_ingestion_service.py:36-49`
- Evidence: Upload, text extraction, chunking, embedding generation, and database writes happen during one API request.
- Impact: Slow provider calls or larger documents can tie up request workers and lead to user-facing timeouts.
- Recommended solution: Use a background worker for ingestion in non-demo deployments, returning an accepted job/document status.
- Estimated implementation complexity: Medium.

### Issue REL-002

- Severity: Medium
- Affected file and line: `app/services/workflow_request_service.py:100-129`
- Evidence: Status updates read and then write without row-level locking or optimistic concurrency.
- Impact: Concurrent status updates could race in a multi-worker deployment.
- Recommended solution: For production, add optimistic locking or transactional row locking for status transitions.
- Estimated implementation complexity: Medium.

### Issue PERF-001

- Severity: Low
- Affected file and line: `alembic/versions/20261004_0003_add_knowledge_documents.py:75-82`
- Evidence: IVFFLAT index is created with fixed `lists=100`.
- Impact: This may be poorly tuned for very small or larger datasets.
- Recommended solution: Document index tuning and run `ANALYZE` after bulk ingestion. Tune lists/probes based on corpus size.
- Estimated implementation complexity: Low.

### Issue OBS-001

- Severity: Low
- Affected file and line: `app/core/logging.py`; `app/workflows/execution.py:14-66`
- Evidence: Basic logging exists, but no request ID/correlation ID, metrics, tracing, or structured workflow audit trail across all workflow types.
- Impact: Debugging production issues would be difficult.
- Recommended solution: Add correlation IDs, structured logs, and minimal metrics for request counts, provider errors, ingestion failures, and workflow outcomes.
- Estimated implementation complexity: Medium.

## K. Missing or Incomplete Features

Mandatory before production/public deployment:

- Authentication and authorization.
- Object-level access control for requests, users, documents, and workflow execution.
- Rate limiting and resource exhaustion controls.
- Real provider integration tests or an explicit manual verification checklist.
- Dependency vulnerability scanning.
- CI pipeline for tests, linting, and security checks.
- Production database extension/permission documentation for pgvector.
- Operational monitoring and logs with correlation IDs.

Optional or portfolio polish:

- Conversation persistence APIs or remove unused conversation model until needed.
- Background jobs for document ingestion and long-running workflows.
- OCR/DOCX ingestion if desired.
- Workflow execution records for all workflow types.
- Coverage report and type checking.
- API examples for every endpoint.

## L. Prioritized Remediation Plan

1. Add authentication and object-level authorization.
   - Priority: Mandatory for production.
   - Complexity: Medium to High.

2. Add rate limiting and request/body-size enforcement at the app and deployment edge.
   - Priority: Mandatory for public deployment.
   - Complexity: Medium.

3. Add a RAG relevance threshold and tests for unrelated queries.
   - Priority: Mandatory for reliable knowledge answers.
   - Complexity: Low to Medium.

4. Add optional live-provider integration tests guarded by environment variables.
   - Priority: Mandatory before claiming real AI E2E support.
   - Complexity: Low.

5. Add CI with pytest, pip check, dependency audit, and optional lint/format checks.
   - Priority: High.
   - Complexity: Low to Medium.

6. Add a dependency lock/constraints file.
   - Priority: High.
   - Complexity: Low.

7. Improve workflow observability.
   - Priority: Medium.
   - Complexity: Medium.

8. Document or clean up legacy enum values.
   - Priority: Medium.
   - Complexity: Medium.

9. Move ingestion and long-running provider calls to background processing.
   - Priority: Medium for production; optional for portfolio.
   - Complexity: Medium.

10. Add PostgreSQL integration test instructions and pgvector migration verification.
    - Priority: Medium.
    - Complexity: Low.

## M. Production Readiness Assessment

| Area | Rating | Notes |
|---|---|---|
| Architecture | Supported | Clean and simple for project scope. Needs async/background design for higher scale. |
| Functional completeness | Partially Supported | Core portfolio features work; auth, live AI E2E verification, and background processing missing. |
| Security | Partially Supported | Good secret/config/error/upload practices, but no authz and no rate limiting. |
| Testing | Supported for local behavior, Partially Supported overall | 92 tests pass; real DB and real provider tests unverified. |
| AI integration | Partially Supported | Provider code and validation exist; live integrations not tested. |
| Reliability | Partially Supported | Timeouts and rollback handling exist; no retries, jobs, concurrency controls, or monitoring. |
| Documentation | Supported | README accurately documents setup, endpoints, limitations, and fake-provider tests. |

Production readiness conclusion: **Conditionally Ready for portfolio/local demo; Not Ready for public production deployment.**

Before the application can be considered production ready, the following must be completed:

- Add authentication and authorization.
- Add rate limiting and deployment-level body-size controls.
- Verify live LLM and embedding integrations with safe test credentials.
- Add RAG relevance thresholds and grounding tests.
- Add dependency vulnerability scanning and reproducible dependency locking.
- Verify migrations against a running PostgreSQL/pgvector instance in CI or a documented local environment.
- Add observability for workflow execution and provider failures.

## N. Verification Limitations

- Docker was not running during this audit. `docker compose ps postgres` failed because the Docker socket was unavailable.
- `alembic current` could not connect to PostgreSQL at `127.0.0.1:5433`, so live database migration state was blocked.
- No paid or external LLM/embedding API calls were made.
- `pip-audit` was not installed, so dependency vulnerability findings are limited to configuration review and `pip check`.
- No destructive tests, load tests, fuzzing, or production-like security testing were performed.
- The audit did not push, commit, refactor, or modify existing application behavior.

