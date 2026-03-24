from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import ApprovalStatus, ApprovalTargetType


class ApprovalCreateRequest(BaseModel):
    target_type: ApprovalTargetType
    target_id: UUID
    note: str | None = Field(default=None, max_length=2000)


class ApprovalReviewRequest(BaseModel):
    status: ApprovalStatus
    review_note: str | None = Field(default=None, max_length=2000)


class ApprovalResponse(BaseModel):
    id: UUID
    matter_id: UUID
    target_type: ApprovalTargetType
    target_id: str
    status: ApprovalStatus
    note: str | None
    review_note: str | None
    requested_by_user_id: UUID
    reviewed_by_user_id: UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class AuditEventResponse(BaseModel):
    id: UUID
    action: str
    entity_type: str
    entity_id: str
    detail: str | None
    created_at: datetime


class InstitutionalDashboardResponse(BaseModel):
    matter_id: UUID
    urgency_status: str
    days_to_hearing: int | None
    pending_approvals: int
    latest_draft_id: UUID | None
    approvals: list[ApprovalResponse]
    recent_audit_events: list[AuditEventResponse]
    plain_language_en: str
    plain_language_hi: str
    low_bandwidth_brief: list[str]
    decision_support_label: str
