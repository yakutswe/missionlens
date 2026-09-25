from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    action_description: str = Field(min_length=10, max_length=1000)


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=10, max_length=1000)


class ApprovalResponse(BaseModel):
    id: UUID
    case_id: UUID
    case_title: str
    action_description: str
    status: ApprovalStatus
    requested_by: str
    decided_by: str | None
    decision_reason: str | None
    created_at: datetime
    decided_at: datetime | None


class AuditEventResponse(BaseModel):
    id: UUID
    case_id: UUID
    approval_id: UUID
    actor_id: str
    event_type: str
    details: str
    occurred_at: datetime
