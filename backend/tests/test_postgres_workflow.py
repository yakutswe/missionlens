"""Opt-in persistence test, run against an isolated PostGIS database in CI."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from backend.app.db.session import SessionLocal
from backend.app.main import app


@pytest.mark.skipif(
    os.getenv("MISSIONLENS_INTEGRATION") != "1",
    reason="Requires an isolated migrated PostGIS database",
)
def test_persist_report_search_and_case_evidence() -> None:
    test_token = f"CI-{uuid4().hex}"
    payload = {
        "external_id": f"{test_token}-A",
        "title": "Synthetic transit observation",
        "content": "A fictional transit report used to verify the persisted case workflow.",
        "language": "en",
        "source_type": "field_report",
        "source_name": "Synthetic test feed",
        "location": {"latitude": 40.7128, "longitude": -74.006},
        "observed_at": "2026-09-22T12:00:00Z",
    }

    with TestClient(app) as client:
        created = client.post("/api/v1/reports", json=payload)
        assert created.status_code == 201
        report_id = created.json()["id"]
        assert client.post("/api/v1/reports", json=payload).status_code == 409

        second_payload = {**payload, "external_id": f"{test_token}-B",
                          "title": "Synthetic platform update"}
        second = client.post("/api/v1/reports", json=second_payload)
        assert second.status_code == 201
        second_id = second.json()["id"]

        search = client.get("/api/v1/reports", params={
            "language": "en",
            "min_latitude": 40.0,
            "max_latitude": 41.0,
            "min_longitude": -75.0,
            "max_longitude": -73.0,
        })
        assert search.status_code == 200
        assert any(report["id"] == report_id for report in search.json())
        assert "en" in client.get("/api/v1/reports/languages").json()

        first_page = client.get("/api/v1/reports", params={"query": test_token, "limit": 1})
        next_page = client.get("/api/v1/reports", params={
            "query": test_token, "limit": 1, "offset": 1,
        })
        assert first_page.headers["x-total-count"] == "2"
        assert first_page.json()[0]["id"] != next_page.json()[0]["id"]
        assert all(
            report["id"] not in {report_id, second_id}
            for report in client.get("/api/v1/reports", params={"query": "%"}).json()
        )

        case = client.post("/api/v1/cases", json={
            "title": "Review synthetic transit",
            "summary": "Review the linked fictional observation before any action.",
            "report_ids": [second_id, report_id],
        })
        assert case.status_code == 201
        assert case.json()["report_titles"] == [
            "Synthetic platform update", "Synthetic transit observation"
        ]
        assert client.get(f"/api/v1/cases/{case.json()['id']}").json() == case.json()
        assert any(
            item["id"] == case.json()["id"] and item["report_titles"] == case.json()["report_titles"]
            for item in client.get("/api/v1/cases").json()
        )

        requested = client.post(f"/api/v1/cases/{case.json()['id']}/approvals", json={
            "action_description": "Review these fictional reports before recommending any follow-up.",
        }, headers={"X-Demo-Actor": "analyst-demo"})
        assert requested.status_code == 201
        assert requested.json()["status"] == "pending"
        decision_url = f"/api/v1/approvals/{requested.json()['id']}/decision"
        decided = client.post(decision_url, json={
            "decision": "rejected", "reason": "The cause is unverified in this synthetic case.",
        }, headers={"X-Demo-Actor": "supervisor-demo"})
        assert decided.status_code == 200
        assert decided.json()["status"] == "rejected"
        assert client.post(decision_url, json={
            "decision": "approved", "reason": "Trying to repeat a decision should fail.",
        }, headers={"X-Demo-Actor": "supervisor-demo"}).status_code == 409
        events = client.get("/api/v1/audit-events", headers={"X-Demo-Actor": "supervisor-demo"}).json()
        assert [event["event_type"] for event in events if event["approval_id"] == requested.json()["id"]] == [
            "approval_rejected", "approval_requested",
        ]

    # Even a direct UPDATE by the application database role must be rejected.
    with SessionLocal() as session:
        with pytest.raises(DBAPIError):
            session.execute(
                text("UPDATE audit_events SET details = 'changed' WHERE id = :id"),
                {"id": events[0]["id"]},
            )
        session.rollback()
