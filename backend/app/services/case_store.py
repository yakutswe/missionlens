from datetime import datetime, timezone
from threading import RLock
from uuid import UUID, uuid4

from backend.app.models.case import CaseCreate, CaseResponse
from backend.app.services.case_repository import CaseNotFoundError, UnknownReportError
from backend.app.services.report_store import ReportStore


class CaseStore:
    """Isolated case repository for API tests; production uses PostgreSQL."""

    def __init__(self, reports: ReportStore) -> None:
        self._reports = reports
        self._cases: dict[UUID, CaseResponse] = {}
        self._lock = RLock()

    def create(self, data: CaseCreate) -> CaseResponse:
        with self._lock:
            for report_id in data.report_ids:
                if not self._reports.has_id(report_id):
                    raise UnknownReportError(report_id)
            case = CaseResponse(
                **data.model_dump(), id=uuid4(), created_at=datetime.now(timezone.utc),
                report_titles=[self._reports.title_for_id(id) for id in data.report_ids],
            )
            self._cases[case.id] = case
            return case

    def get(self, case_id: UUID) -> CaseResponse:
        with self._lock:
            if case_id not in self._cases:
                raise CaseNotFoundError(case_id)
            return self._cases[case_id]

    def list_all(self) -> list[CaseResponse]:
        with self._lock:
            return sorted(self._cases.values(), key=lambda case: case.created_at, reverse=True)

    def clear(self) -> None:
        with self._lock:
            self._cases.clear()
