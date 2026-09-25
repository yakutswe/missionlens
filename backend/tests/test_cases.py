from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import get_case_repository, get_report_repository
from backend.app.main import app
from backend.app.services.case_store import CaseStore
from backend.app.services.report_store import ReportStore

client = TestClient(app)
reports = ReportStore()
cases = CaseStore(reports)


@pytest.fixture(autouse=True)
def isolated_repositories() -> Generator[None, None, None]:
    app.dependency_overrides[get_report_repository] = lambda: reports
    app.dependency_overrides[get_case_repository] = lambda: cases
    reports.clear()
    cases.clear()
    yield
    cases.clear()
    reports.clear()
    app.dependency_overrides.pop(get_report_repository, None)
    app.dependency_overrides.pop(get_case_repository, None)


def make_report(external_id: str) -> str:
    response = client.post("/api/v1/reports", json={
        "external_id": external_id,
        "title": f"Synthetic field observation {external_id}",
        "content": "This is a synthetic observation created for case workflow testing.",
        "language": "en",
        "source_type": "field_report",
        "source_name": "Synthetic Team",
        "location": {"latitude": 40.0, "longitude": -74.0},
        "observed_at": "2026-09-22T18:30:00Z",
    })
    assert response.status_code == 201
    return response.json()["id"]


def test_create_case_preserves_report_evidence_order() -> None:
    first = make_report("CASE-001")
    second = make_report("CASE-002")
    response = client.post("/api/v1/cases", json={
        "title": "Investigate synthetic event",
        "summary": "Compare the two synthetic reports before taking any action.",
        "report_ids": [second, first],
    })
    assert response.status_code == 201
    case = response.json()
    assert case["report_ids"] == [second, first]
    assert case["report_titles"] == [
        "Synthetic field observation CASE-002", "Synthetic field observation CASE-001"
    ]
    assert case["created_at"]
    assert client.get(f"/api/v1/cases/{case['id']}").json() == case
    assert client.get("/api/v1/cases").json() == [case]


def test_unknown_report_rejects_whole_case() -> None:
    first = make_report("CASE-001")
    missing = str(uuid4())
    response = client.post("/api/v1/cases", json={
        "title": "Investigate synthetic event",
        "summary": "No partial case should be created if evidence is missing.",
        "report_ids": [first, missing],
    })
    assert response.status_code == 422
    assert response.json()["detail"] == {"code": "unknown_report", "report_id": missing}
    assert client.get("/api/v1/cases").json() == []


def test_duplicate_evidence_is_rejected() -> None:
    first = make_report("CASE-001")
    response = client.post("/api/v1/cases", json={
        "title": "Investigate synthetic event",
        "summary": "Duplicate evidence should not be accepted in a case.",
        "report_ids": [first, first],
    })
    assert response.status_code == 422


def test_missing_case_returns_not_found() -> None:
    assert client.get(f"/api/v1/cases/{uuid4()}").status_code == 404
