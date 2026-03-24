from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import DraftDocumentType, DraftStatus


class StylePackCreateRequest(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    description: str | None = None
    tone: str = Field(default="formal and restrained", min_length=3, max_length=255)
    opening_phrase: str = Field(
        default="It is most respectfully submitted",
        min_length=3,
        max_length=255,
    )
    prayer_style: str = Field(
        default="It is therefore most respectfully prayed",
        min_length=3,
        max_length=255,
    )
    citation_style: str = Field(default="anchor-plus-checksum", min_length=3, max_length=255)
    voice_notes: str | None = None
    source_document_ids: list[UUID] = Field(default_factory=list)


class StylePackResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    tone: str
    opening_phrase: str
    prayer_style: str
    citation_style: str
    voice_notes: str | None
    sample_document_titles: str | None
    created_at: datetime


class DraftGenerateRequest(BaseModel):
    document_type: DraftDocumentType
    title: str | None = None
    style_pack_id: UUID | None = None
    annexure_document_ids: list[UUID] = Field(default_factory=list)
    include_saved_authorities: bool = True
    include_bundle_intelligence: bool = True


class DraftSectionResponse(BaseModel):
    id: UUID
    section_key: str
    label: str
    body_text: str
    order_index: int
    is_required: bool
    placeholder_count: int


class DraftAuthorityUseResponse(BaseModel):
    id: UUID
    saved_authority_id: UUID
    issue_label: str
    treatment: str
    section_key: str
    anchor_label: str
    quote_text: str
    checksum: str
    citation_text: str | None


class DraftAnnexureResponse(BaseModel):
    id: UUID
    label: str
    title: str
    note: str | None
    source_document_id: UUID | None


class DraftDocumentResponse(BaseModel):
    id: UUID
    matter_id: UUID
    title: str
    document_type: DraftDocumentType
    status: DraftStatus
    version_number: int
    summary: str | None
    export_file_name: str | None
    style_pack: StylePackResponse | None
    sections: list[DraftSectionResponse]
    authorities_used: list[DraftAuthorityUseResponse]
    annexures: list[DraftAnnexureResponse]
    unresolved_placeholders: list[str]
    created_at: datetime


class DraftExportResponse(BaseModel):
    file_name: str
    content: str


class DraftRedlineSectionResponse(BaseModel):
    section_key: str
    label: str
    diff: str


class DraftRedlineResponse(BaseModel):
    current_draft_id: UUID
    previous_draft_id: UUID
    sections: list[DraftRedlineSectionResponse]
