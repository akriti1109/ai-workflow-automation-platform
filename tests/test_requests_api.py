from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import RequestPriority, RequestStatus, RequestType
from app.models.user import User
from app.models.workflow_request import WorkflowRequest


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
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def user(db_session: Session) -> User:
    user = User(name="Akriti Sharma", email="akriti@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_request(
    db_session: Session,
    user_id: int,
    request_type: RequestType = RequestType.ACCESS_REQUEST,
    status: RequestStatus = RequestStatus.PENDING,
    original_request: str = "Please create this request.",
) -> WorkflowRequest:
    workflow_request = WorkflowRequest(
        user_id=user_id,
        request_type=request_type,
        original_request=original_request,
        status=status,
        priority=RequestPriority.MEDIUM,
    )
    db_session.add(workflow_request)
    db_session.commit()
    db_session.refresh(workflow_request)
    return workflow_request


def test_create_request_success(client: TestClient, user: User) -> None:
    response = client.post(
        "/api/v1/requests",
        json={
            "user_id": user.id,
            "request_type": "access_request",
            "original_request": "I need access to Salesforce.",
            "priority": "high",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == user.id
    assert data["request_type"] == "access_request"
    assert data["original_request"] == "I need access to Salesforce."
    assert data["status"] == "pending"
    assert data["priority"] == "high"


def test_create_request_rejects_invalid_input(client: TestClient, user: User) -> None:
    response = client.post(
        "/api/v1/requests",
        json={
            "user_id": user.id,
            "request_type": "invalid_type",
            "original_request": "",
        },
    )

    assert response.status_code == 422


def test_get_existing_request(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    workflow_request = create_request(db_session, user.id)

    response = client.get(f"/api/v1/requests/{workflow_request.id}")

    assert response.status_code == 200
    assert response.json()["id"] == workflow_request.id


def test_get_missing_request_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/requests/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WORKFLOW_REQUEST_NOT_FOUND"


def test_list_requests(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    create_request(db_session, user.id, original_request="First request")
    create_request(db_session, user.id, original_request="Second request")

    response = client.get("/api/v1/requests")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_requests_supports_pagination(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    create_request(db_session, user.id, original_request="First request")
    create_request(db_session, user.id, original_request="Second request")
    create_request(db_session, user.id, original_request="Third request")

    response = client.get("/api/v1/requests?limit=2&offset=1")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["items"]) == 2


def test_list_requests_supports_status_filter(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    create_request(db_session, user.id, status=RequestStatus.PENDING)
    create_request(db_session, user.id, status=RequestStatus.FAILED)

    response = client.get("/api/v1/requests?status=failed")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "failed"


def test_list_requests_supports_request_type_filter(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    create_request(db_session, user.id, request_type=RequestType.ACCESS_REQUEST)
    create_request(db_session, user.id, request_type=RequestType.KNOWLEDGE_QUERY)

    response = client.get("/api/v1/requests?request_type=knowledge_query")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["request_type"] == "knowledge_query"


def test_update_request_status_with_valid_transition(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    workflow_request = create_request(db_session, user.id)

    response = client.patch(
        f"/api/v1/requests/{workflow_request.id}/status",
        json={"status": "processing"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_update_request_status_rejects_invalid_transition(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    workflow_request = create_request(db_session, user.id)

    response = client.patch(
        f"/api/v1/requests/{workflow_request.id}/status",
        json={"status": "completed"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STATUS_TRANSITION"


def test_update_missing_request_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/requests/999/status",
        json={"status": "processing"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WORKFLOW_REQUEST_NOT_FOUND"

