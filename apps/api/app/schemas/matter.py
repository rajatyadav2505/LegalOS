from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import MatterStage, MatterStatus


class MatterSummaryResponse(BaseModel):
    id: UUID
    title: str
    reference_code: str
    forum: str
    stage: MatterStage
    status: MatterStatus
    next_hearing_date: date | None
    summary: str | None
    updated_at: datetime
    document_count: int
    saved_authority_count: int


class MatterDetailResponse(MatterSummaryResponse):
    organization_id: UUID
    owner_user_id: UUID
