from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.domain.enums import (
    ArtifactKind,
    ConfidenceBand,
    EventType,
    FilingSide,
    PartyRole,
    SourceSystem,
    VerificationStatus,
)


class ImportedIdentifier(BaseModel):
    identifier_type: str
    identifier_value: str
    is_primary: bool = False


class ImportedParty(BaseModel):
    role: PartyRole
    display_name: str
    aliases: list[str] = Field(default_factory=list)


class ImportedCounsel(BaseModel):
    counsel_name: str
    side_label: str | None = None
    aliases: list[str] = Field(default_factory=list)


class ImportedEvent(BaseModel):
    event_type: EventType
    event_date: date
    title: str
    description: str
    source_anchor: str | None = None
    judge_name: str | None = None


class ImportedListing(BaseModel):
    listing_date: date
    purpose: str | None = None
    item_number: str | None = None
    bench_label: str | None = None
    court_hall: str | None = None
    judge_name: str | None = None


class ImportedFiling(BaseModel):
    filing_side: FilingSide
    filing_type: str
    title: str
    filing_date: date | None = None
    reliefs_sought: list[str] = Field(default_factory=list)
    fact_assertions: list[str] = Field(default_factory=list)
    admissions: list[str] = Field(default_factory=list)
    denials: list[str] = Field(default_factory=list)
    annexures_relied: list[str] = Field(default_factory=list)
    statutes_cited: list[str] = Field(default_factory=list)
    precedents_cited: list[str] = Field(default_factory=list)
    extracted_summary: str | None = None


class ImportedDeadline(BaseModel):
    due_date: date
    title: str
    status_text: str | None = None
    detail: str | None = None


class ImportedArtifact(BaseModel):
    artifact_kind: ArtifactKind
    title: str
    summary: str | None = None
    neutral_citation: str | None = None


class ImportedConnectedCase(BaseModel):
    relation_label: str
    case_number: str
    title: str
    note: str | None = None


class ImportedCaseData(BaseModel):
    source_system: SourceSystem
    artifact_kind: ArtifactKind
    title: str
    case_number: str
    cnr_number: str | None = None
    case_type: str | None = None
    filing_number: str | None = None
    filing_date: date | None = None
    registration_date: date | None = None
    status_text: str | None = None
    subject: str | None = None
    neutral_citation: str | None = None
    latest_stage: str | None = None
    next_listing_date: date | None = None
    court_name: str
    court_type: str | None = None
    establishment_name: str | None = None
    establishment_code: str | None = None
    district_name: str | None = None
    state_name: str | None = None
    bench_label: str | None = None
    court_hall: str | None = None
    judge_name: str | None = None
    source_url: str | None = None
    observed_at: datetime | None = None
    fetched_at: datetime
    content_hash: str
    parser_version: str
    confidence: ConfidenceBand
    verification_status: VerificationStatus
    identifiers: list[ImportedIdentifier] = Field(default_factory=list)
    parties: list[ImportedParty] = Field(default_factory=list)
    counsels: list[ImportedCounsel] = Field(default_factory=list)
    events: list[ImportedEvent] = Field(default_factory=list)
    listings: list[ImportedListing] = Field(default_factory=list)
    filings: list[ImportedFiling] = Field(default_factory=list)
    deadlines: list[ImportedDeadline] = Field(default_factory=list)
    artifacts: list[ImportedArtifact] = Field(default_factory=list)
    connected_cases: list[ImportedConnectedCase] = Field(default_factory=list)
