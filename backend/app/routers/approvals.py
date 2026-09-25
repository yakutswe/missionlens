from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.demo_actor import DemoActor, get_demo_actor, require_role
from backend.app.dependencies import get_approval_repository
from backend.app.models.approval import (
    ApprovalCreate, ApprovalDecision, ApprovalResponse, AuditEventResponse,
)
from backend.app.services.approval_repository import (
    AlreadyDecidedError, ApprovalRepository, MissingApprovalError, MissingCaseError, SelfApprovalError,
)

router = APIRouter(tags=["local demo approvals"])
Repository = Annotated[ApprovalRepository, Depends(get_approval_repository)]
Actor = Annotated[DemoActor, Depends(get_demo_actor)]


@router.post("/api/v1/cases/{case_id}/approvals", response_model=ApprovalResponse,
             status_code=status.HTTP_201_CREATED)
def request_approval(case_id: UUID, data: ApprovalCreate, repository: Repository, actor: Actor) -> ApprovalResponse:
    require_role(actor, "analyst")
    try:
        return repository.create(case_id, data, actor.id)
    except MissingCaseError as error:
        raise HTTPException(status_code=404, detail="Case not found") from error


@router.get("/api/v1/approvals", response_model=list[ApprovalResponse])
def list_approvals(repository: Repository, actor: Actor) -> list[ApprovalResponse]:
    return repository.list_all()


@router.post("/api/v1/approvals/{approval_id}/decision", response_model=ApprovalResponse)
def decide_approval(approval_id: UUID, data: ApprovalDecision,
                    repository: Repository, actor: Actor) -> ApprovalResponse:
    require_role(actor, "supervisor")
    try:
        return repository.decide(approval_id, data, actor.id)
    except MissingApprovalError as error:
        raise HTTPException(status_code=404, detail="Approval request not found") from error
    except AlreadyDecidedError as error:
        raise HTTPException(status_code=409, detail="Approval already decided") from error
    except SelfApprovalError as error:
        raise HTTPException(status_code=403, detail="Requester cannot decide their own action") from error


@router.get("/api/v1/audit-events", response_model=list[AuditEventResponse])
def list_audit_events(repository: Repository, actor: Actor,
                      limit: Annotated[int, Query(ge=1, le=100)] = 100) -> list[AuditEventResponse]:
    require_role(actor, "supervisor")
    return repository.audit_events(limit=limit)
