from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import DocumentSourceType, MatterStage, MatterStatus, ProcessingStatus


class BundleDocumentSummaryResponse(BaseModel):
    id: UUID
    title: str
    source_type: DocumentSourceType
    processing_status: ProcessingStatus
    legal_issue: str | None
    created_at: datetime
    processing_stage: str | None = None
    processing_progress: int | None = None
    processing_error: str | None = None


class BundleProcessingStageResponse(BaseModel):
    label: str
    status: ProcessingStatus
    count: int


class BundleProcessingOverviewResponse(BaseModel):
    overall_status: ProcessingStatus
    total_documents: int
    processed_documents: int
    ready_documents: int
    failed_documents: int
    processing_documents: int
    queued_documents: int
    last_updated_at: datetime
    stages: list[BundleProcessingStageResponse]


class BundleChronologyItemResponse(BaseModel):
    id: UUID
    date: date
    title: str
    summary: str
    source_title: str
    source_type: DocumentSourceType
    anchor_label: str
    confidence: float


class BundleContradictionResponse(BaseModel):
    id: UUID
    issue: str
    severity: str
    summary: str
    contradiction_kind: str
    source_a: str
    source_b: str
    source_a_label: str
    source_b_label: str
    source_a_type: DocumentSourceType
    source_b_type: DocumentSourceType


class BundleClusterResponse(BaseModel):
    id: str
    cluster_type: str
    label: str
    description: str
    document_count: int
    dominant_issue: str
    source_type: DocumentSourceType
    status: str


class BundleDuplicateMemberResponse(BaseModel):
    id: UUID
    title: str
    anchor_label: str


class BundleDuplicateGroupResponse(BaseModel):
    id: str
    canonical_title: str
    duplicate_count: int
    reason: str
    source_type: DocumentSourceType
    members: list[BundleDuplicateMemberResponse]


class BundleExhibitLinkResponse(BaseModel):
    id: UUID
    exhibit_label: str
    title: str
    source_type: DocumentSourceType
    anchor_label: str
    target_title: str
    note: str


class BundleMapResponse(BaseModel):
    matter_id: UUID
    matter_title: str
    matter_reference_code: str
    forum: str
    stage: MatterStage
    matter_status: MatterStatus
    ingestion: BundleProcessingOverviewResponse
    chronology: list[BundleChronologyItemResponse]
    contradictions: list[BundleContradictionResponse]
    clusters: list[BundleClusterResponse]
    duplicate_groups: list[BundleDuplicateGroupResponse]
    exhibit_links: list[BundleExhibitLinkResponse]
    documents: list[BundleDocumentSummaryResponse]
