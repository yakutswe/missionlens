from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import CaseRecord, CaseReportRecord, ReportRecord
from backend.app.models.case import CaseCreate, CaseResponse
from backend.app.services.case_repository import CaseNotFoundError, UnknownReportError


class PostgresCaseStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, data: CaseCreate) -> CaseResponse:
        existing = set(self._session.scalars(
            select(ReportRecord.id).where(ReportRecord.id.in_(data.report_ids))
        ))
        for report_id in data.report_ids:
            if report_id not in existing:
                raise UnknownReportError(report_id)

        record = CaseRecord(title=data.title, summary=data.summary)
        try:
            self._session.add(record)
            self._session.flush()
            self._session.add_all([
                CaseReportRecord(case_id=record.id, report_id=report_id, position=index)
                for index, report_id in enumerate(data.report_ids)
            ])
            self._session.commit()
            self._session.refresh(record)
        except Exception:
            self._session.rollback()
            raise
        return self._response(record)

    def get(self, case_id: UUID) -> CaseResponse:
        record = self._session.get(CaseRecord, case_id)
        if record is None:
            raise CaseNotFoundError(case_id)
        return self._response(record)

    def list_all(self) -> list[CaseResponse]:
        records = self._session.scalars(
            select(CaseRecord).order_by(CaseRecord.created_at.desc(), CaseRecord.id)
        ).all()
        evidence = self._evidence([record.id for record in records])
        return [self._response(record, evidence.get(record.id, [])) for record in records]

    def _evidence(self, case_ids: list[UUID]) -> dict[UUID, list[tuple[UUID, str]]]:
        if not case_ids:
            return {}
        rows = self._session.execute(
            select(CaseReportRecord.case_id, CaseReportRecord.report_id, ReportRecord.title)
            .join(ReportRecord, CaseReportRecord.report_id == ReportRecord.id)
            .where(CaseReportRecord.case_id.in_(case_ids))
            .order_by(CaseReportRecord.case_id, CaseReportRecord.position)
        )
        evidence: dict[UUID, list[tuple[UUID, str]]] = {}
        for case_id, report_id, title in rows:
            evidence.setdefault(case_id, []).append((report_id, title))
        return evidence

    def _response(
        self, record: CaseRecord, links: list[tuple[UUID, str]] | None = None
    ) -> CaseResponse:
        if links is None:
            links = self._evidence([record.id]).get(record.id, [])
        return CaseResponse(
            id=record.id,
            title=record.title,
            summary=record.summary,
            report_ids=[report_id for report_id, _ in links],
            report_titles=[title for _, title in links],
            created_at=record.created_at,
        )
