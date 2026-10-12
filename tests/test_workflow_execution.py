from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.providers import LLMProviderError, LLMProviderTimeout
from app.api.ai import get_llm_provider
from app.core.errors import AppError
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import RequestStatus, RequestType, WorkflowExecutionStatus
from app.models.user import User
from app.models.workflow_execution import WorkflowExecution
from app.models.workflow_request import WorkflowRequest
from app.schemas.ai import AIIntent
from app.core.config import Settings
from app.knowledge.constants import DEFAULT_EMBEDDING_DIMENSION
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.services.workflow_orchestrator import execute_workflow
from app.workflows.router import get_workflow_handler


class FakeProvider:
    def __init__(
        self,
        response: dict[str, object] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or {}
        self.error = error

    def extract_intent(self, text: str) -> dict[str, object]:
        if self.error is not None:
            raise self.error
        return self.response

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "Use the access portal to request application access."


class FakeEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] + [0.0] * (DEFAULT_EMBEDDING_DIMENSION - 1) for _ in texts]


def build_settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://user:password@localhost:5432/db",
        rag_top_k=2,
    )


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    with TestingSessionLocal() as session:
        yield session


@pytest.fixture()
def user(db_session: Session) -> User:
    user = User(name="Akriti Sharma", email="akriti.workflow@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_existing_request(db_session: Session, user_id: int) -> WorkflowRequest:
    workflow_request = WorkflowRequest(
        user_id=user_id,
        request_type=RequestType.ACCESS_REQUEST,
        original_request="Need access.",
        status=RequestStatus.PROCESSING,
    )
    db_session.add(workflow_request)
    db_session.commit()
    db_session.refresh(workflow_request)
    return workflow_request


def workflow_request_count(db_session: Session) -> int:
    return db_session.scalar(select(func.count()).select_from(WorkflowRequest)) or 0


def workflow_execution_count(db_session: Session) -> int:
    return db_session.scalar(select(func.count()).select_from(WorkflowExecution)) or 0


def test_access_request_workflow_success(db_session: Session, user: User) -> None:
    result = execute_workflow(
        db_session,
        FakeProvider(
            {
                "intent": "access_request",
                "priority": "high",
                "entities": {"application": "finance"},
            }
        ),
        user.id,
        "I need access to the finance application.",
    )

    assert result.success is True
    assert result.intent is AIIntent.ACCESS_REQUEST
    assert result.request_type is RequestType.ACCESS_REQUEST
    assert result.status == "pending"
    assert result.request_id is not None


def test_support_request_workflow_success(db_session: Session, user: User) -> None:
    result = execute_workflow(
        db_session,
        FakeProvider(
            {
                "intent": "support_request",
                "priority": "medium",
                "entities": {"issue": "Laptop disconnecting from Wi-Fi"},
            }
        ),
        user.id,
        "My laptop keeps disconnecting from Wi-Fi.",
    )

    assert result.success is True
    assert result.request_type is RequestType.SUPPORT_REQUEST
    assert result.status == "pending"


def test_request_status_lookup_success(db_session: Session, user: User) -> None:
    existing_request = create_existing_request(db_session, user.id)

    result = execute_workflow(
        db_session,
        FakeProvider(
            {
                "intent": "request_status",
                "priority": "medium",
                "entities": {"request_id": existing_request.id},
            }
        ),
        user.id,
        f"What is the status of request {existing_request.id}?",
    )

    assert result.success is True
    assert result.intent is AIIntent.REQUEST_STATUS
    assert result.request_id == existing_request.id
    assert result.status == "processing"


def test_request_status_for_missing_request(db_session: Session, user: User) -> None:
    with pytest.raises(AppError) as exc_info:
        execute_workflow(
            db_session,
            FakeProvider(
                {
                    "intent": "request_status",
                    "priority": "medium",
                    "entities": {"request_id": 999},
                }
            ),
            user.id,
            "What is the status of request 999?",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "WORKFLOW_REQUEST_NOT_FOUND"


def test_knowledge_query_uses_rag(db_session: Session, user: User) -> None:
    document = KnowledgeDocument(
        original_filename="it-policy.txt",
        content_type="text/plain",
        size_bytes=40,
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(
        KnowledgeChunk(
            document_id=document.id,
            chunk_index=0,
            content="Use the access portal to request application access.",
            embedding=[1.0] + [0.0] * (DEFAULT_EMBEDDING_DIMENSION - 1),
        )
    )
    db_session.commit()

    result = execute_workflow(
        db_session,
        FakeProvider(
            {
                "intent": "knowledge_query",
                "priority": "low",
                "entities": {"question": "How do I reset my password?"},
            }
        ),
        user.id,
        "How do I reset my password?",
        build_settings(),
        FakeEmbeddingProvider(),
    )

    assert result.success is True
    assert result.status == "completed"
    assert result.sources[0].filename == "it-policy.txt"
    assert workflow_request_count(db_session) == 0


def test_unknown_intent(db_session: Session, user: User) -> None:
    result = execute_workflow(
        db_session,
        FakeProvider(
            {
                "intent": "unknown",
                "priority": "medium",
                "entities": {"reason": "unclear"},
            }
        ),
        user.id,
        "Please do the thing.",
    )

    assert result.success is False
    assert result.status == "unsupported_intent"
    assert workflow_request_count(db_session) == 0


def test_missing_user(db_session: Session) -> None:
    with pytest.raises(AppError) as exc_info:
        execute_workflow(
            db_session,
            FakeProvider(
                {
                    "intent": "access_request",
                    "priority": "medium",
                    "entities": {"application": "finance"},
                }
            ),
            999,
            "I need access.",
        )

    assert exc_info.value.error_code == "USER_NOT_FOUND"
    assert workflow_request_count(db_session) == 0


def test_missing_required_access_application(
    db_session: Session,
    user: User,
) -> None:
    with pytest.raises(AppError) as exc_info:
        execute_workflow(
            db_session,
            FakeProvider(
                {
                    "intent": "access_request",
                    "priority": "medium",
                    "entities": {},
                }
            ),
            user.id,
            "I need access.",
        )

    assert exc_info.value.error_code == "MISSING_REQUIRED_ENTITY"
    assert workflow_request_count(db_session) == 0


def test_missing_support_issue(db_session: Session, user: User) -> None:
    with pytest.raises(AppError) as exc_info:
        execute_workflow(
            db_session,
            FakeProvider(
                {
                    "intent": "support_request",
                    "priority": "medium",
                    "entities": {},
                }
            ),
            user.id,
            "I need help.",
        )

    assert exc_info.value.error_code == "MISSING_REQUIRED_ENTITY"
    assert workflow_request_count(db_session) == 0


def test_invalid_request_id(db_session: Session, user: User) -> None:
    with pytest.raises(AppError) as exc_info:
        execute_workflow(
            db_session,
            FakeProvider(
                {
                    "intent": "request_status",
                    "priority": "medium",
                    "entities": {"request_id": 0},
                }
            ),
            user.id,
            "What is the status of request 0?",
        )

    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"


def test_correct_workflow_routing() -> None:
    assert get_workflow_handler(AIIntent.ACCESS_REQUEST).__name__ == "handle_access_request"
    assert get_workflow_handler(AIIntent.SUPPORT_REQUEST).__name__ == "handle_support_request"
    assert get_workflow_handler(AIIntent.REQUEST_STATUS).__name__ == "handle_request_status"


def test_unsupported_routing_value() -> None:
    with pytest.raises(AppError) as exc_info:
        get_workflow_handler("unsupported")  # type: ignore[arg-type]

    assert exc_info.value.error_code == "UNSUPPORTED_WORKFLOW_INTENT"


def test_workflow_creates_correct_workflow_request(
    db_session: Session,
    user: User,
) -> None:
    result = execute_workflow(
        db_session,
        FakeProvider(
            {
                "intent": "support_request",
                "priority": "urgent",
                "entities": {"issue": "VPN is down"},
            }
        ),
        user.id,
        "VPN is down.",
    )

    workflow_request = db_session.get(WorkflowRequest, result.request_id)
    assert workflow_request is not None
    assert workflow_request.user_id == user.id
    assert workflow_request.request_type is RequestType.SUPPORT_REQUEST
    assert workflow_request.priority.value == "urgent"
    assert workflow_request.original_request == "VPN is down."


def test_workflow_records_execution(db_session: Session, user: User) -> None:
    result = execute_workflow(
        db_session,
        FakeProvider(
            {
                "intent": "access_request",
                "priority": "medium",
                "entities": {"application": "finance"},
            }
        ),
        user.id,
        "Need finance access.",
    )

    execution = db_session.scalar(
        select(WorkflowExecution).where(
            WorkflowExecution.request_id == result.request_id
        )
    )
    assert execution is not None
    assert execution.action == "create_access_request"
    assert execution.status is WorkflowExecutionStatus.COMPLETED


def test_ai_timeout_does_not_create_request(
    db_session: Session,
    user: User,
) -> None:
    with pytest.raises(AppError):
        execute_workflow(
            db_session,
            FakeProvider(error=LLMProviderTimeout("timeout")),
            user.id,
            "Need access.",
        )

    assert workflow_request_count(db_session) == 0


def test_invalid_ai_response_does_not_create_request(
    db_session: Session,
    user: User,
) -> None:
    with pytest.raises(AppError):
        execute_workflow(
            db_session,
            FakeProvider({"intent": "access_request"}),
            user.id,
            "Need access.",
        )

    assert workflow_request_count(db_session) == 0


def test_failed_workflow_does_not_leave_partial_state(
    db_session: Session,
    user: User,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_record_execution(*args: object, **kwargs: object) -> None:
        raise SQLAlchemyError("write failed")

    monkeypatch.setattr(
        "app.workflows.execution.record_execution",
        fail_record_execution,
    )

    with pytest.raises(AppError) as exc_info:
        execute_workflow(
            db_session,
            FakeProvider(
                {
                    "intent": "access_request",
                    "priority": "medium",
                    "entities": {"application": "finance"},
                }
            ),
            user.id,
            "Need finance access.",
        )

    assert exc_info.value.error_code == "DATABASE_ERROR"
    assert workflow_request_count(db_session) == 0
    assert workflow_execution_count(db_session) == 0


def test_execute_endpoint_success(
    client: TestClient,
    user: User,
) -> None:
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(
        {
            "intent": "access_request",
            "priority": "medium",
            "entities": {"application": "finance"},
        }
    )

    response = client.post(
        "/api/v1/workflows/execute",
        json={"user_id": user.id, "text": "I need finance access."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "access_request"
    assert data["success"] is True
    assert data["request_id"] is not None
    assert data["status"] == "pending"


def test_execute_endpoint_failure(
    client: TestClient,
    user: User,
) -> None:
    app.dependency_overrides[get_llm_provider] = lambda: FakeProvider(
        error=LLMProviderError("provider failed")
    )

    response = client.post(
        "/api/v1/workflows/execute",
        json={"user_id": user.id, "text": "I need help."},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_PROVIDER_ERROR"
