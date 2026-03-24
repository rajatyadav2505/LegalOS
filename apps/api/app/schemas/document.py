from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import AuthorityKind, DocumentSourceType, ProcessingStatus


class DocumentResponse(BaseModel):
    id: UUID
    matter_id: UUID | None
    title: str
    file_name: str
    content_type: str
    source_type: DocumentSourceType
    processing_status: ProcessingStatus
    authority_kind: AuthorityKind
    citation_text: str | None
    court: str | None
    forum: str | None
    bench: str | None
    decision_date: date | None
    legal_issue: str | None
    processing_stage: str | None = None
    processing_progress: int | None = None
    extraction_method: str | None = None
    processing_error: str | None = None
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    created_at: datetime
