from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import ApprovalRequestRecord, AuditEventRecord, CaseRecord
from backend.app.models.approval import (
    ApprovalCreate, ApprovalDecision, ApprovalResponse, ApprovalStatus, AuditEventResponse,
)
from backend.app.services.approval_repository import (
    AlreadyDecidedError, MissingApprovalError, MissingCaseError, SelfApprovalError,
)


class PostgresApprovalStore:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, case_id: UUID, data: ApprovalCreate, actor_id: str) -> ApprovalResponse:
        case = self._session.get(CaseRecord, case_id)
        if case is None:
            raise MissingCaseError
        record = ApprovalRequestRecord(
            case_id=case_id, action_description=data.action_description,
            status=ApprovalStatus.PENDING.value, requested_by=actor_id,
        )
        try:
            self._session.add(record)
            self._session.flush()
            self._session.add(AuditEventRecord(
                case_id=case_id, approval_id=record.id, actor_id=actor_id,
                event_type="approval_requested", details=data.action_description,
            ))
            self._session.commit()
            self._session.refresh(record)
        except Exception:
            self._session.rollback()
            raise
        return self._response(record, case.title)

    def decide(self, approval_id: UUID, data: ApprovalDecision, actor_id: str) -> ApprovalResponse:
        try:
            record = self._session.scalar(
                select(ApprovalRequestRecord)
                .where(ApprovalRequestRecord.id == approval_id)
                .with_for_update()
            )
            if record is None:
                raise MissingApprovalError
            if record.status != ApprovalStatus.PENDING.value:
                raise AlreadyDecidedError
            if record.requested_by == actor_id:
                raise SelfApprovalError
            record.status = data.decision
            record.decided_by = actor_id
            record.decision_reason = data.reason
            record.decided_at = datetime.now(timezone.utc)
            self._session.add(AuditEventRecord(
                case_id=record.case_id, approval_id=approval_id, actor_id=actor_id,
                event_type=f"approval_{data.decision}", details=data.reason,
            ))
            self._session.commit()
            self._session.refresh(record)
        except Exception:
            self._session.rollback()
            raise
        case = self._session.get(CaseRecord, record.case_id)
        assert case is not None
        return self._response(record, case.title)

    def list_all(self) -> list[ApprovalResponse]:
        rows = self._session.execute(
            select(ApprovalRequestRecord, CaseRecord.title)
            .join(CaseRecord, ApprovalRequestRecord.case_id == CaseRecord.id)
            .order_by(ApprovalRequestRecord.created_at.desc(), ApprovalRequestRecord.id.desc())
        )
        return [self._response(record, title) for record, title in rows]

    def audit_events(self, limit: int = 100) -> list[AuditEventResponse]:
        records = self._session.scalars(
            select(AuditEventRecord)
            .order_by(AuditEventRecord.occurred_at.desc(), AuditEventRecord.id.desc())
            .limit(limit)
        )
        return [AuditEventResponse(
            id=record.id, case_id=record.case_id, approval_id=record.approval_id,
            actor_id=record.actor_id, event_type=record.event_type,
            details=record.details, occurred_at=record.occurred_at,
        ) for record in records]

    @staticmethod
    def _response(record: ApprovalRequestRecord, case_title: str) -> ApprovalResponse:
        return ApprovalResponse(
            id=record.id, case_id=record.case_id, case_title=case_title,
            action_description=record.action_description,
            status=ApprovalStatus(record.status), requested_by=record.requested_by,
            decided_by=record.decided_by, decision_reason=record.decision_reason,
            created_at=record.created_at, decided_at=record.decided_at,
        )
