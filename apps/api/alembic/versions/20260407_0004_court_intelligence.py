"""court intelligence orchestration and public docket models

Revision ID: 20260407_0004
Revises: 20260324_0003
Create Date: 2026-04-07 15:30:00
"""

from __future__ import annotations

from alembic import op
from app.domain.court_intelligence import (
    Bench,
    CaseCounsel,
    CaseDeadline,
    CaseEvent,
    CaseFiling,
    CaseListing,
    CaseMemorySnapshot,
    CaseParty,
    CauseListEntry,
    CaveatEntry,
    CounselAlias,
    Court,
    CourtArtifact,
    CourtEstablishment,
    CourtProfileSnapshot,
    ExternalCase,
    ExternalCaseIdentifier,
    ExternalCaseLink,
    HybridIndexEntry,
    Judge,
    JudgeAssignment,
    JudgeProfileSnapshot,
    LitigantMemorySnapshot,
    MatterExternalCaseLink,
    ParserRun,
    Party,
    PartyAlias,
    PartyRelationship,
    PublicSourceSnapshot,
    RegistryEvent,
    SourceFetchLog,
)
from app.domain.jobs import Job, JobArtifact, JobAttempt, ModelRun, PromptRun

revision = "20260407_0004"
down_revision = "20260324_0003"
branch_labels = None
depends_on = None


TABLES = [
    Court.__table__,
    CourtEstablishment.__table__,
    Bench.__table__,
    Judge.__table__,
    PublicSourceSnapshot.__table__,
    Job.__table__,
    JobAttempt.__table__,
    JobArtifact.__table__,
    PromptRun.__table__,
    ModelRun.__table__,
    Party.__table__,
    PartyAlias.__table__,
    PartyRelationship.__table__,
    ExternalCase.__table__,
    ExternalCaseIdentifier.__table__,
    MatterExternalCaseLink.__table__,
    ExternalCaseLink.__table__,
    JudgeAssignment.__table__,
    CourtArtifact.__table__,
    CaseParty.__table__,
    CaseCounsel.__table__,
    CounselAlias.__table__,
    CaseEvent.__table__,
    CaseListing.__table__,
    CauseListEntry.__table__,
    CaseFiling.__table__,
    RegistryEvent.__table__,
    CaseDeadline.__table__,
    CaveatEntry.__table__,
    LitigantMemorySnapshot.__table__,
    CaseMemorySnapshot.__table__,
    JudgeProfileSnapshot.__table__,
    CourtProfileSnapshot.__table__,
    SourceFetchLog.__table__,
    ParserRun.__table__,
    HybridIndexEntry.__table__,
]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    for table in TABLES:
        table.create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed(TABLES):
        table.drop(bind, checkfirst=True)
