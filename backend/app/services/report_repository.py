from typing import Protocol

from backend.app.models.report import (
    ReportCreate,
    ReportResponse,
    SourceType,
)


class DuplicateReportError(Exception):
    """Raised when a source submits the same external report twice."""

    def __init__(self, external_id: str) -> None:
        self.external_id = external_id
        super().__init__(
            f"A report with external_id '{external_id}' already exists."
        )


class ReportRepository(Protocol):
    """Storage contract used by the reports API."""

    def create(
        self,
        report_data: ReportCreate,
    ) -> ReportResponse:
        ...

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
        ...