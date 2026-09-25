from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app.dependencies import (
    get_approval_repository, get_case_repository, get_report_repository,
)
from backend.app.main import app
from backend.app.services.approval_store import ApprovalStore
from backend.app.services.case_store import CaseStore
from backend.app.services.report_store import ReportStore

client = TestClient(app)
reports = ReportStore()
cases = CaseStore(reports)
approvals = ApprovalStore(cases)
analyst = {"X-Demo-Actor": "analyst-demo"}
supervisor = {"X-Demo-Actor": "supervisor-demo"}


@pytest.fixture(autouse=True)
def isolated_repositories() -> Generator[None, None, None]:
    app.dependency_overrides[get_report_repository] = lambda: reports
    app.dependency_overrides[get_case_repository] = lambda: cases
    app.dependency_overrides[get_approval_repository] = lambda: approvals
    reports.clear()
    cases.clear()
    approvals.clear()
    yield
    approvals.clear()
    cases.clear()
    reports.clear()
    for dependency in (get_report_repository, get_case_repository, get_approval_repository):
        app.dependency_overrides.pop(dependency, None)


def create_case() -> str:
    report = client.post("/api/v1/reports", json={
        "external_id": "APPROVAL-TEST-001", "title": "Synthetic report for approval",
        "content": "A fictional event to test the supervisor approval workflow.",
        "language": "en", "source_type": "field_report", "source_name": "Synthetic feed",
        "location": {"latitude": 40.7128, "longitude": -74.006},
        "observed_at": "2026-09-22T12:00:00Z",
    })
    assert report.status_code == 201
    case = client.post("/api/v1/cases", json={
        "title": "Review fictional report",
        "summary": "Review the linked report before proposing any action.",
        "report_ids": [report.json()["id"]],
    })
    assert case.status_code == 201
    return case.json()["id"]


def test_approval_requires_role_and_writes_one_audit_event_per_transition() -> None:
    case_id = create_case()
    url = f"/api/v1/cases/{case_id}/approvals"
    payload = {"action_description": "Request further review of the fictional terminal reports."}
    assert client.post(url, json=payload).status_code == 401
    assert client.post(url, json=payload, headers=supervisor).status_code == 403
    assert client.post(f"/api/v1/cases/{uuid4()}/approvals", json=payload, headers=analyst).status_code == 404

    created = client.post(url, json=payload, headers=analyst)
    assert created.status_code == 201
    assert created.json()["status"] == "pending"
    approval_id = created.json()["id"]
    decision_url = f"/api/v1/approvals/{approval_id}/decision"
    decision = {"decision": "approved", "reason": "Sources reviewed for this fictional case."}
    assert client.post(decision_url, json=decision, headers=analyst).status_code == 403
    assert client.post(decision_url, json={**decision, "decision": "pending"}, headers=supervisor).status_code == 422

    decided = client.post(decision_url, json=decision, headers=supervisor)
    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"
    assert decided.json()["decided_by"] == "supervisor-demo"
    assert client.post(decision_url, json=decision, headers=supervisor).status_code == 409

    assert client.get("/api/v1/audit-events", headers=analyst).status_code == 403
    events = client.get("/api/v1/audit-events", headers=supervisor).json()
    assert [event["event_type"] for event in events] == ["approval_approved", "approval_requested"]
    assert all(event["approval_id"] == approval_id for event in events)
    assert len(client.get("/api/v1/approvals", headers=analyst).json()) == 1


def test_rejection_records_reason_and_does_not_execute_action() -> None:
    case_id = create_case()
    created = client.post(f"/api/v1/cases/{case_id}/approvals", headers=analyst,
                          json={"action_description": "Investigate the fictional access delay."})
    approval_id = created.json()["id"]
    result = client.post(f"/api/v1/approvals/{approval_id}/decision", headers=supervisor,
                         json={"decision": "rejected", "reason": "Evidence does not establish the cause."})
    assert result.status_code == 200
    assert result.json()["status"] == "rejected"
    assert result.json()["decision_reason"] == "Evidence does not establish the cause."
    assert client.get("/api/v1/audit-events", headers=supervisor).json()[0]["event_type"] == "approval_rejected"
