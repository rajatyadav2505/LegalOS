from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import AuthorityKind, AuthorityTreatment, DocumentSourceType


class ResearchSearchResult(BaseModel):
    document_id: UUID
    quote_span_id: UUID
    title: str
    citation_text: str | None
    authority_kind: AuthorityKind
    source_type: DocumentSourceType
    court: str | None
    forum: str | None
    bench: str | None
    decision_date: date | None
    legal_issue: str | None
    anchor_label: str
    paragraph_start: int
    paragraph_end: int
    page_start: int | None
    page_end: int | None
    quote_text: str
    quote_checksum: str
    score: float
    saved_treatment: AuthorityTreatment | None = None


class ResearchSearchResponse(BaseModel):
    items: list[ResearchSearchResult]
    total: int


class SaveAuthorityRequest(BaseModel):
    quote_span_id: UUID
    citation_id: UUID | None = None
    treatment: AuthorityTreatment
    issue_label: str = Field(min_length=3, max_length=255)
    note: str | None = None


class SavedAuthorityResponse(BaseModel):
    id: UUID
    matter_id: UUID
    quote_span_id: UUID
    citation_id: UUID | None
    treatment: AuthorityTreatment
    issue_label: str
    note: str | None


class QuoteLockResponse(BaseModel):
    quote_span_id: UUID
    anchor_label: str
    text: str
    checksum: str


class ExportMemoResponse(BaseModel):
    file_name: str
    content: str
