from datetime import datetime, timezone
from threading import RLock
from uuid import UUID, uuid4

from backend.app.models.approval import (
    ApprovalCreate, ApprovalDecision, ApprovalResponse, ApprovalStatus, AuditEventResponse,
)
from backend.app.services.approval_repository import (
    AlreadyDecidedError, MissingApprovalError, MissingCaseError, SelfApprovalError,
)
from backend.app.services.case_repository import CaseNotFoundError
from backend.app.services.case_store import CaseStore


class ApprovalStore:
    """Isolated test implementation of the approval repository."""

    def __init__(self, cases: CaseStore) -> None:
        self._cases = cases
        self._approvals: dict[UUID, ApprovalResponse] = {}
        self._events: list[AuditEventResponse] = []
        self._lock = RLock()

    def create(self, case_id: UUID, data: ApprovalCreate, actor_id: str) -> ApprovalResponse:
        with self._lock:
            try:
                case = self._cases.get(case_id)
            except CaseNotFoundError as error:
                raise MissingCaseError from error
            approval = ApprovalResponse(
                id=uuid4(), case_id=case_id, case_title=case.title,
                action_description=data.action_description, status=ApprovalStatus.PENDING,
                requested_by=actor_id, decided_by=None, decision_reason=None,
                created_at=datetime.now(timezone.utc), decided_at=None,
            )
            self._approvals[approval.id] = approval
            self._events.append(AuditEventResponse(
                id=uuid4(), case_id=case_id, approval_id=approval.id,
                actor_id=actor_id, event_type="approval_requested",
                details=data.action_description, occurred_at=datetime.now(timezone.utc),
            ))
            return approval

    def decide(self, approval_id: UUID, data: ApprovalDecision, actor_id: str) -> ApprovalResponse:
        with self._lock:
            approval = self._approvals.get(approval_id)
            if approval is None:
                raise MissingApprovalError
            if approval.status != ApprovalStatus.PENDING:
                raise AlreadyDecidedError
            if approval.requested_by == actor_id:
                raise SelfApprovalError
            decided = approval.model_copy(update={
                "status": ApprovalStatus(data.decision), "decided_by": actor_id,
                "decision_reason": data.reason, "decided_at": datetime.now(timezone.utc),
            })
            self._approvals[approval_id] = decided
            self._events.append(AuditEventResponse(
                id=uuid4(), case_id=approval.case_id, approval_id=approval_id,
                actor_id=actor_id, event_type=f"approval_{data.decision}",
                details=data.reason, occurred_at=datetime.now(timezone.utc),
            ))
            return decided

    def list_all(self) -> list[ApprovalResponse]:
        with self._lock:
            return sorted(self._approvals.values(), key=lambda approval: (approval.created_at, approval.id), reverse=True)

    def audit_events(self, limit: int = 100) -> list[AuditEventResponse]:
        with self._lock:
            return sorted(self._events, key=lambda event: (event.occurred_at, event.id), reverse=True)[:limit]

    def clear(self) -> None:
        with self._lock:
            self._approvals.clear()
            self._events.clear()
