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
        return [self._response(record) for record in records]

    def _response(self, record: CaseRecord) -> CaseResponse:
        report_ids = list(self._session.scalars(
            select(CaseReportRecord.report_id)
            .where(CaseReportRecord.case_id == record.id)
            .order_by(CaseReportRecord.position)
        ))
        return CaseResponse(
            id=record.id,
            title=record.title,
            summary=record.summary,
            report_ids=report_ids,
            created_at=record.created_at,
        )
