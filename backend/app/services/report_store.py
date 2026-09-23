from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from backend.app.models.report import (
    ReportCreate,
    ReportResponse,
    ReportStatus,
)


class DuplicateReportError(Exception):
    """Raised when a source submits the same external report twice."""

    def __init__(self, external_id: str) -> None:
        self.external_id = external_id
        super().__init__(
            f"A report with external_id '{external_id}' already exists."
        )


class ReportStore:
    """Thread-safe in-memory storage for the first MissionLens slice."""

    def __init__(self) -> None:
        self._reports_by_external_id: dict[str, ReportResponse] = {}
        self._lock = RLock()

    def create(self, report_data: ReportCreate) -> ReportResponse:
        with self._lock:
            if report_data.external_id in self._reports_by_external_id:
                raise DuplicateReportError(report_data.external_id)

            report = ReportResponse(
                **report_data.model_dump(),
                id=uuid4(),
                status=ReportStatus.RECEIVED,
                ingested_at=datetime.now(timezone.utc),
            )

            self._reports_by_external_id[report.external_id] = report

            return report

    def list_all(self) -> list[ReportResponse]:
        with self._lock:
            reports = list(self._reports_by_external_id.values())

        return sorted(
            reports,
            key=lambda report: report.ingested_at,
            reverse=True,
        )

    def clear(self) -> None:
        """Reset the temporary store between automated tests."""

        with self._lock:
            self._reports_by_external_id.clear()


report_store = ReportStore()