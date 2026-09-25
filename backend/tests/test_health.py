from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from backend.app.db.session import get_db_session
from backend.app.main import app


client = TestClient(app)


def test_health_check_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "missionlens-api"
    assert payload["version"] == "0.1.0"
    assert payload["timestamp"]


def test_readiness_checks_database_and_reports_unavailability() -> None:
    class ConnectedSession:
        def execute(self, statement: object) -> int:
            return 1

    class DisconnectedSession:
        def execute(self, statement: object) -> None:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    try:
        app.dependency_overrides[get_db_session] = lambda: ConnectedSession()
        assert client.get("/ready").json() == {"status": "ready"}

        app.dependency_overrides[get_db_session] = lambda: DisconnectedSession()
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
    finally:
        app.dependency_overrides.pop(get_db_session, None)
