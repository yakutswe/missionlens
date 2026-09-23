from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4
from backend.app.services.report_repository import DuplicateReportError
from backend.app.models.report import (
    ReportCreate,
    ReportResponse,
    ReportStatus,
    SourceType,
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
        return self.search()

    def search(
        self,
        *,
        language: str | None = None,
        source_type: SourceType | None = None,
        min_latitude: float | None = None,
        max_latitude: float | None = None,
        min_longitude: float | None = None,
        max_longitude: float | None = None,
    ) -> list[ReportResponse]:
        with self._lock:
            reports = list(self._reports_by_external_id.values())

        if language is not None:
            reports = [
                report
                for report in reports
                if report.language == language
            ]

        if source_type is not None:
            reports = [
                report
                for report in reports
                if report.source_type == source_type
            ]

        coordinates = (
            min_latitude,
            max_latitude,
            min_longitude,
            max_longitude,
        )

        if all(value is not None for value in coordinates):
            assert min_latitude is not None
            assert max_latitude is not None
            assert min_longitude is not None
            assert max_longitude is not None

            reports = [
                report
                for report in reports
                if (
                    min_latitude
                    <= report.location.latitude
                    <= max_latitude
                    and min_longitude
                    <= report.location.longitude
                    <= max_longitude
                )
            ]

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