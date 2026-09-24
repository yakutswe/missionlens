from typing import Protocol
from uuid import UUID

from backend.app.models.case import CaseCreate, CaseResponse


class UnknownReportError(Exception):
    def __init__(self, report_id: UUID) -> None:
        self.report_id = report_id
        super().__init__(f"Report '{report_id}' does not exist.")


class CaseNotFoundError(Exception):
    def __init__(self, case_id: UUID) -> None:
        self.case_id = case_id
        super().__init__(f"Case '{case_id}' does not exist.")


class CaseRepository(Protocol):
    def create(self, data: CaseCreate) -> CaseResponse: ...

    def get(self, case_id: UUID) -> CaseResponse: ...

    def list_all(self) -> list[CaseResponse]: ...
