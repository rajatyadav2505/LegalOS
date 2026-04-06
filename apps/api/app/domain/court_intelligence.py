from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import EmbeddingVectorType
from app.domain.enums import (
    ArtifactKind,
    ConfidenceBand,
    EventType,
    FilingSide,
    HybridEntityKind,
    PartyRole,
    ProfileWindow,
    SourceSystem,
    VerificationStatus,
)

if TYPE_CHECKING:
    from app.domain.document import Document
    from app.domain.jobs import Job
    from app.domain.matter import Matter
    from app.domain.organization import Organization
    from app.domain.user import User


class PublicRecordMixin:
    source_system: Mapped[SourceSystem] = mapped_column(Enum(SourceSystem), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    raw_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("public_source_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    parser_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[ConfidenceBand] = mapped_column(
        Enum(ConfidenceBand),
        nullable=False,
        default=ConfidenceBand.MEDIUM,
        server_default=ConfidenceBand.MEDIUM.name,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.IMPORTED,
        server_default=VerificationStatus.IMPORTED.name,
    )


class Court(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "courts"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_courts_slug"),
        Index("ix_courts_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    court_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    official_website: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class CourtEstablishment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "court_establishments"
    __table_args__ = (
        UniqueConstraint("court_id", "code", name="uq_court_establishments_court_code"),
    )

    court_id: Mapped[UUID] = mapped_column(
        ForeignKey("courts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    district_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    state_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    official_website: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    court: Mapped[Court] = relationship()


class Bench(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "benches"
    __table_args__ = (
        UniqueConstraint("court_id", "label", name="uq_benches_court_label"),
    )

    court_id: Mapped[UUID] = mapped_column(
        ForeignKey("courts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    establishment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("court_establishments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    bench_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    court_hall: Mapped[str | None] = mapped_column(String(64), nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)

    court: Mapped[Court] = relationship()
    establishment: Mapped[CourtEstablishment | None] = relationship()


class Judge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "judges"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_judges_normalized_name"),
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    honorific: Mapped[str | None] = mapped_column(String(64), nullable=True)


class JudgeAssignment(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "judge_assignments"
    __table_args__ = (
        Index("ix_judge_assignments_org_judge", "organization_id", "judge_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    judge_id: Mapped[UUID] = mapped_column(
        ForeignKey("judges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    court_id: Mapped[UUID] = mapped_column(
        ForeignKey("courts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bench_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("benches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role_title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    organization: Mapped[Organization] = relationship()
    judge: Mapped[Judge] = relationship()
    court: Mapped[Court] = relationship()
    bench: Mapped[Bench | None] = relationship()


class ExternalCase(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "external_cases"
    __table_args__ = (
        Index("ix_external_cases_org_cnr", "organization_id", "cnr_number"),
        Index("ix_external_cases_org_case_number", "organization_id", "case_number"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    court_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("courts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    establishment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("court_establishments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bench_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("benches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    current_judge_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("judges.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    case_number: Mapped[str] = mapped_column(String(255), nullable=False)
    cnr_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    case_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    filing_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    registration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    neutral_citation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latest_stage: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_listing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped[Organization] = relationship()
    court: Mapped[Court | None] = relationship()
    establishment: Mapped[CourtEstablishment | None] = relationship()
    bench: Mapped[Bench | None] = relationship()
    current_judge: Mapped[Judge | None] = relationship()


class ExternalCaseIdentifier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "external_case_identifiers"
    __table_args__ = (
        UniqueConstraint(
            "external_case_id",
            "identifier_type",
            "identifier_value",
            name="uq_external_case_identifiers_case_value",
        ),
    )

    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identifier_type: Mapped[str] = mapped_column(String(64), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    external_case: Mapped[ExternalCase] = relationship()


class ExternalCaseLink(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "external_case_links"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "left_case_id",
            "right_case_id",
            "relation_label",
            name="uq_external_case_links_pair",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    left_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    right_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_label: Mapped[str] = mapped_column(String(128), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship()
    left_case: Mapped[ExternalCase] = relationship(foreign_keys=[left_case_id])
    right_case: Mapped[ExternalCase] = relationship(foreign_keys=[right_case_id])


class MatterExternalCaseLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matter_external_case_links"
    __table_args__ = (
        UniqueConstraint("matter_id", "external_case_id", name="uq_matter_external_case_links"),
    )

    matter_id: Mapped[UUID] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    linked_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_label: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="primary",
        server_default="primary",
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    matter: Mapped[Matter] = relationship()
    external_case: Mapped[ExternalCase] = relationship()
    linked_by: Mapped[User] = relationship()


class Party(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "parties"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "normalized_name",
            name="uq_parties_org_normalized_name",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    party_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

    organization: Mapped[Organization] = relationship()


class PartyAlias(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "party_aliases"
    __table_args__ = (
        UniqueConstraint("party_id", "normalized_alias", name="uq_party_aliases_party_alias"),
    )

    party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False)

    party: Mapped[Party] = relationship()


class CaseParty(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "case_parties"
    __table_args__ = (
        UniqueConstraint(
            "external_case_id",
            "party_id",
            "role",
            name="uq_case_parties_case_party_role",
        ),
    )

    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[PartyRole] = mapped_column(Enum(PartyRole), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    side_label: Mapped[str | None] = mapped_column(String(128), nullable=True)

    external_case: Mapped[ExternalCase] = relationship()
    party: Mapped[Party] = relationship()


class CaseCounsel(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "case_counsels"
    __table_args__ = (
        UniqueConstraint(
            "external_case_id",
            "normalized_name",
            "side_label",
            name="uq_case_counsels_case_name_side",
        ),
    )

    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("parties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    counsel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    side_label: Mapped[str | None] = mapped_column(String(128), nullable=True)

    external_case: Mapped[ExternalCase] = relationship()
    party: Mapped[Party | None] = relationship()


class CounselAlias(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "counsel_aliases"
    __table_args__ = (
        UniqueConstraint(
            "case_counsel_id",
            "normalized_alias",
            name="uq_counsel_aliases_case_counsel_alias",
        ),
    )

    case_counsel_id: Mapped[UUID] = mapped_column(
        ForeignKey("case_counsels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_alias: Mapped[str] = mapped_column(String(255), nullable=False)

    case_counsel: Mapped[CaseCounsel] = relationship()


class PartyRelationship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "party_relationships"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    left_party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    right_party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_label: Mapped[str] = mapped_column(String(128), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship()
    left_party: Mapped[Party] = relationship(foreign_keys=[left_party_id])
    right_party: Mapped[Party] = relationship(foreign_keys=[right_party_id])


class PublicSourceSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "public_source_snapshots"
    __table_args__ = (
        Index("ix_public_source_snapshots_org_source", "organization_id", "source_system"),
        Index("ix_public_source_snapshots_content_hash", "content_hash"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_system: Mapped[SourceSystem] = mapped_column(Enum(SourceSystem), nullable=False)
    artifact_kind: Mapped[ArtifactKind] = mapped_column(Enum(ArtifactKind), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    import_method: Mapped[str] = mapped_column(String(64), nullable=False)

    organization: Mapped[Organization] = relationship()
    uploaded_by: Mapped[User | None] = relationship()


class SourceFetchLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "source_fetch_logs"

    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    raw_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("public_source_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_system: Mapped[SourceSystem] = mapped_column(Enum(SourceSystem), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    request_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    organization: Mapped[Organization | None] = relationship()
    raw_snapshot: Mapped[PublicSourceSnapshot | None] = relationship()


class ParserRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "parser_runs"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    raw_snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("public_source_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parser_name: Mapped[str] = mapped_column(String(128), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped[Organization] = relationship()
    raw_snapshot: Mapped[PublicSourceSnapshot] = relationship()


class CourtArtifact(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "court_artifacts"
    __table_args__ = (
        Index("ix_court_artifacts_case_kind", "external_case_id", "artifact_kind"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("matters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    artifact_kind: Mapped[ArtifactKind] = mapped_column(Enum(ArtifactKind), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    neutral_citation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    organization: Mapped[Organization] = relationship()
    matter: Mapped[Matter | None] = relationship()
    external_case: Mapped[ExternalCase] = relationship()
    document: Mapped[Document | None] = relationship()


class CaseEvent(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "case_events"
    __table_args__ = (
        Index("ix_case_events_case_date", "external_case_id", "event_date"),
        Index("ix_case_events_event_type", "event_type"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    court_artifact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("court_artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    judge_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("judges.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_anchor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_latest_for_type: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()
    court_artifact: Mapped[CourtArtifact | None] = relationship()
    judge: Mapped[Judge | None] = relationship()


class CaseListing(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "case_listings"
    __table_args__ = (
        Index("ix_case_listings_case_date", "external_case_id", "listing_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bench_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("benches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    judge_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("judges.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    listing_date: Mapped[date] = mapped_column(Date, nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    court_hall: Mapped[str | None] = mapped_column(String(64), nullable=True)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()
    bench: Mapped[Bench | None] = relationship()
    judge: Mapped[Judge | None] = relationship()


class CauseListEntry(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "cause_list_entries"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_listing_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("case_listings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    court_artifact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("court_artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entry_text: Mapped[str] = mapped_column(Text, nullable=False)
    item_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()
    case_listing: Mapped[CaseListing | None] = relationship()
    court_artifact: Mapped[CourtArtifact | None] = relationship()


class CaseFiling(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "case_filings"
    __table_args__ = (
        Index("ix_case_filings_case_date", "external_case_id", "filing_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    court_artifact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("court_artifacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filing_side: Mapped[FilingSide] = mapped_column(Enum(FilingSide), nullable=False)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    filing_type: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reliefs_sought: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    fact_assertions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    admissions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    denials: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    annexures_relied: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    statutes_cited: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    precedents_cited: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    extracted_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()
    court_artifact: Mapped[CourtArtifact | None] = relationship()


class RegistryEvent(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "registry_events"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()


class CaseDeadline(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "case_deadlines"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()


class CaveatEntry(UUIDPrimaryKeyMixin, TimestampMixin, PublicRecordMixin, Base):
    __tablename__ = "caveat_entries"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    caveator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()


class LitigantMemorySnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "litigant_memory_snapshots"
    __table_args__ = (
        Index("ix_litigant_memory_snapshots_party_created", "party_id", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_id: Mapped[UUID] = mapped_column(
        ForeignKey("parties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    generated_by_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    source_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    confidence: Mapped[ConfidenceBand] = mapped_column(Enum(ConfidenceBand), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        nullable=False,
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped[Organization] = relationship()
    party: Mapped[Party] = relationship()
    generated_by_job: Mapped[Job | None] = relationship()


class CaseMemorySnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "case_memory_snapshots"
    __table_args__ = (
        Index("ix_case_memory_snapshots_case_created", "external_case_id", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_case_id: Mapped[UUID] = mapped_column(
        ForeignKey("external_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("matters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    generated_by_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    source_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    confidence: Mapped[ConfidenceBand] = mapped_column(Enum(ConfidenceBand), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        nullable=False,
    )
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped[Organization] = relationship()
    external_case: Mapped[ExternalCase] = relationship()
    matter: Mapped[Matter | None] = relationship()
    generated_by_job: Mapped[Job | None] = relationship()


class JudgeProfileSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "judge_profile_snapshots"
    __table_args__ = (
        Index("ix_judge_profile_snapshots_judge_created", "judge_id", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    judge_id: Mapped[UUID] = mapped_column(
        ForeignKey("judges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    court_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("courts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    generated_by_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    window: Mapped[ProfileWindow] = mapped_column(Enum(ProfileWindow), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    freshness_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence: Mapped[ConfidenceBand] = mapped_column(Enum(ConfidenceBand), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped[Organization] = relationship()
    judge: Mapped[Judge] = relationship()
    court: Mapped[Court | None] = relationship()
    generated_by_job: Mapped[Job | None] = relationship()


class CourtProfileSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "court_profile_snapshots"
    __table_args__ = (
        Index("ix_court_profile_snapshots_court_created", "court_id", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    court_id: Mapped[UUID] = mapped_column(
        ForeignKey("courts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    generated_by_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    window: Mapped[ProfileWindow] = mapped_column(Enum(ProfileWindow), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    freshness_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence: Mapped[ConfidenceBand] = mapped_column(Enum(ConfidenceBand), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    source_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped[Organization] = relationship()
    court: Mapped[Court] = relationship()
    generated_by_job: Mapped[Job | None] = relationship()


class HybridIndexEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hybrid_index_entries"
    __table_args__ = (
        Index("ix_hybrid_index_entries_org_kind", "organization_id", "entity_kind"),
        Index("ix_hybrid_index_entries_matter", "matter_id"),
        Index("ix_hybrid_index_entries_external_case", "external_case_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("matters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_case_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("external_cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    party_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("parties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    judge_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("judges.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    court_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("courts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_kind: Mapped[HybridEntityKind] = mapped_column(Enum(HybridEntityKind), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_anchor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVectorType(dimensions=16))
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    organization: Mapped[Organization] = relationship()
    matter: Mapped[Matter | None] = relationship()
    external_case: Mapped[ExternalCase | None] = relationship()
    party: Mapped[Party | None] = relationship()
    judge: Mapped[Judge | None] = relationship()
    court: Mapped[Court | None] = relationship()
