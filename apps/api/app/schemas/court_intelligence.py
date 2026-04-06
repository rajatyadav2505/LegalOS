from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import (
    ArtifactKind,
    ConfidenceBand,
    HybridEntityKind,
    JobKind,
    JobStatus,
    SourceSystem,
    VerificationStatus,
)


class JobResponse(BaseModel):
    id: UUID
    kind: JobKind
    status: JobStatus
    idempotency_key: str
    attempt_count: int
    max_attempts: int
    last_error: str | None
    created_at: datetime
    completed_at: datetime | None


class ExternalCaseLinkRequest(BaseModel):
    source_system: SourceSystem
    case_title: str
    case_number: str
    court_name: str
    cnr_number: str | None = None
    source_url: str | None = None
    relationship_label: str = "primary"


class ProvenanceResponse(BaseModel):
    source_system: SourceSystem
    source_url: str | None
    raw_snapshot_id: UUID | None
    observed_at: datetime | None
    fetched_at: datetime | None
    content_hash: str | None
    parser_version: str | None
    confidence: ConfidenceBand
    verification_status: VerificationStatus


class ExternalCaseSummaryResponse(BaseModel):
    id: UUID
    matter_link_id: UUID | None = None
    court_id: UUID | None = None
    judge_id: UUID | None = None
    title: str
    case_number: str
    cnr_number: str | None
    case_type: str | None
    court_name: str | None
    bench_label: str | None
    judge_name: str | None
    status_text: str | None
    neutral_citation: str | None
    latest_stage: str | None
    next_listing_date: date | None
    relationship_label: str | None = None
    is_primary: bool = False
    provenance: ProvenanceResponse


class CasePartySummaryResponse(BaseModel):
    party_id: UUID
    display_name: str
    role: str


class MatterExternalCaseListResponse(BaseModel):
    items: list[ExternalCaseSummaryResponse]
    total: int


class MergedChronologyItemResponse(BaseModel):
    id: str
    event_date: date
    title: str
    description: str
    source_kind: str
    source_label: str
    confidence: float | str
    provenance: dict[str, str] | None = None


class HearingDeltaResponse(BaseModel):
    summary: str
    changed_items: list[str]
    latest_event_date: date | None


class FilingLineageDeltaResponse(BaseModel):
    new_fact_assertions: list[str]
    new_denials: list[str]


class FilingLineageItemResponse(BaseModel):
    id: str
    external_case_id: str
    case_number: str
    filing_side: str
    filing_type: str
    title: str
    filing_date: date | None
    reliefs_sought: list[str]
    fact_assertions: list[str]
    admissions: list[str]
    denials: list[str]
    annexures_relied: list[str]
    statutes_cited: list[str]
    precedents_cited: list[str]
    extracted_summary: str | None
    delta: FilingLineageDeltaResponse


class MemorySnapshotResponse(BaseModel):
    id: UUID
    storage_path: str
    markdown_content: str
    source_refs: list[dict[str, object]]
    confidence: ConfidenceBand
    verification_status: VerificationStatus
    created_at: datetime


class ProfileSnapshotResponse(BaseModel):
    id: UUID
    storage_path: str
    markdown_content: str
    source_refs: list[dict[str, object]]
    confidence: ConfidenceBand
    sample_size: int
    freshness_timestamp: datetime | None
    metrics: dict[str, object]
    created_at: datetime


class HybridSearchItemResponse(BaseModel):
    title: str
    entity_kind: HybridEntityKind
    score: float
    metadata: dict[str, object]


class HybridSearchResponse(BaseModel):
    items: list[HybridSearchItemResponse]
    total: int


class ConnectedMatterResponse(BaseModel):
    id: UUID
    title: str
    case_number: str
    cnr_number: str | None
    court_name: str | None
    next_listing_date: date | None


class ImportArtifactMetadataResponse(BaseModel):
    source_system: SourceSystem
    artifact_kind: ArtifactKind
    external_case_id: UUID
    snapshot_id: UUID | None


class BenchBriefResponse(BaseModel):
    external_case_id: UUID
    court_name: str | None
    bench_label: str | None
    judge_name: str | None
    next_listing_date: date | None
    status_text: str | None
    sample_size: int | None = None
    freshness_timestamp: datetime | None = None
    confidence: ConfidenceBand | None = None
    notes: list[str] = Field(default_factory=list)
