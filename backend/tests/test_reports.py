from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.report_store import report_store
from backend.app.dependencies import get_report_repository

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_report_store() -> Generator[None, None, None]:
    app.dependency_overrides[get_report_repository] = (
        lambda: report_store
    )
    report_store.clear()

    yield

    report_store.clear()
    app.dependency_overrides.pop(
        get_report_repository,
        None,
    )
def sample_report() -> dict[str, object]:
    return {
        "external_id": "TR-IST-2026-001",
        "title": "Synthetic maritime activity report",
        "content": (
            "İstanbul yakınlarında olağandışı deniz trafiği "
            "gözlemlendi. Bu tamamen sentetik bir rapordur."
        ),
        "language": "tr",
        "source_type": "field_report",
        "source_name": "Synthetic Regional Team",
        "location": {
            "latitude": 41.0082,
            "longitude": 28.9784,
        },
        "observed_at": "2026-09-22T18:30:00Z",
    }

def sample_english_report() -> dict[str, object]:
    return {
        "external_id": "US-NYC-2026-002",
        "title": "Synthetic infrastructure report",
        "content": (
            "A synthetic infrastructure event was observed "
            "near New York City for testing purposes."
        ),
        "language": "en",
        "source_type": "open_source",
        "source_name": "Synthetic Open Source Feed",
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        "observed_at": "2026-09-22T19:00:00Z",
    }
    
def test_create_multilingual_report() -> None:
    response = client.post("/api/v1/reports", json=sample_report())

    assert response.status_code == 201

    payload = response.json()

    assert payload["external_id"] == "TR-IST-2026-001"
    assert payload["language"] == "tr"
    assert payload["status"] == "received"
    assert payload["location"]["latitude"] == 41.0082
    assert payload["id"]
    assert payload["ingested_at"]


def test_list_reports_returns_ingested_report() -> None:
    create_response = client.post(
        "/api/v1/reports",
        json=sample_report(),
    )

    assert create_response.status_code == 201

    list_response = client.get("/api/v1/reports")

    assert list_response.status_code == 200

    reports = list_response.json()

    assert len(reports) == 1
    assert reports[0]["external_id"] == "TR-IST-2026-001"


def test_duplicate_external_id_returns_conflict() -> None:
    first_response = client.post(
        "/api/v1/reports",
        json=sample_report(),
    )
    second_response = client.post(
        "/api/v1/reports",
        json=sample_report(),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    detail = second_response.json()["detail"]

    assert detail["code"] == "duplicate_report"
    assert detail["external_id"] == "TR-IST-2026-001"


def test_invalid_latitude_is_rejected() -> None:
    report = sample_report()
    report["location"] = {
        "latitude": 120.0,
        "longitude": 28.9784,
    }

    response = client.post("/api/v1/reports", json=report)

    assert response.status_code == 422


def test_timestamp_without_timezone_is_rejected() -> None:
    report = sample_report()
    report["observed_at"] = "2026-09-22T18:30:00"

    response = client.post("/api/v1/reports", json=report)

    assert response.status_code == 422
def test_filter_reports_by_language() -> None:
    client.post("/api/v1/reports", json=sample_report())
    client.post("/api/v1/reports", json=sample_english_report())

    response = client.get(
        "/api/v1/reports",
        params={"language": "tr"},
    )

    assert response.status_code == 200

    reports = response.json()

    assert len(reports) == 1
    assert reports[0]["language"] == "tr"


def test_filter_reports_by_source_type() -> None:
    client.post("/api/v1/reports", json=sample_report())
    client.post("/api/v1/reports", json=sample_english_report())

    response = client.get(
        "/api/v1/reports",
        params={"source_type": "open_source"},
    )

    assert response.status_code == 200

    reports = response.json()

    assert len(reports) == 1
    assert reports[0]["external_id"] == "US-NYC-2026-002"


def test_filter_reports_by_geographic_bounding_box() -> None:
    client.post("/api/v1/reports", json=sample_report())
    client.post("/api/v1/reports", json=sample_english_report())

    response = client.get(
        "/api/v1/reports",
        params={
            "min_latitude": 40.5,
            "max_latitude": 41.5,
            "min_longitude": 28.0,
            "max_longitude": 30.0,
        },
    )

    assert response.status_code == 200

    reports = response.json()

    assert len(reports) == 1
    assert reports[0]["external_id"] == "TR-IST-2026-001"


def test_search_with_no_matches_returns_empty_list() -> None:
    client.post("/api/v1/reports", json=sample_report())

    response = client.get(
        "/api/v1/reports",
        params={"language": "es"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_incomplete_bounding_box_is_rejected() -> None:
    response = client.get(
        "/api/v1/reports",
        params={
            "min_latitude": 40.0,
            "max_latitude": 42.0,
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]["code"]
        == "incomplete_bounding_box"
    )


def test_reversed_latitude_range_is_rejected() -> None:
    response = client.get(
        "/api/v1/reports",
        params={
            "min_latitude": 42.0,
            "max_latitude": 40.0,
            "min_longitude": 28.0,
            "max_longitude": 30.0,
        },
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]["code"]
        == "invalid_latitude_range"
    )