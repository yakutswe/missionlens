from fastapi.testclient import TestClient

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
    