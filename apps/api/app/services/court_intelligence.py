from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.court_intelligence import (
    CaseCounsel,
    CaseDeadline,
    CaseEvent,
    CaseFiling,
    CaseListing,
    CaseMemorySnapshot,
    CaseParty,
    CauseListEntry,
    CourtArtifact,
    CourtProfileSnapshot,
    ExternalCase,
    Judge,
    JudgeProfileSnapshot,
    MatterExternalCaseLink,
    Party,
    PublicSourceSnapshot,
)
from app.domain.document import Document
from app.domain.enums import (
    ArtifactKind,
    AuthorityKind,
    ConfidenceBand,
    DocumentSourceType,
    EventType,
    FilingSide,
    HybridEntityKind,
    PartyRole,
    SourceSystem,
    VerificationStatus,
)
from app.integrations.indian_courts.models import ImportedCaseData
from app.repositories.audit import AuditRepository
from app.repositories.court_intelligence import CourtIntelligenceRepository
from app.repositories.jobs import JobRepository
from app.services.ingestion import IngestionMetadata, IngestionService
from app.services.intelligence_agents import (
    ChronologyAgent,
    DraftingPlannerAgent,
    ExtractAgent,
    FetchAgent,
    MemoryArtifactBuilder,
    NormalizeAgent,
    PartyResolutionAgent,
    ProfileAgent,
    QualityGuardAgent,
    RetrievalAgent,
)
from app.services.storage import LocalFilesystemStorage


@dataclass(slots=True)
class LinkExternalCaseRequest:
    source_system: SourceSystem
    case_title: str
    case_number: str
    court_name: str
    cnr_number: str | None = None
    source_url: str | None = None
    relationship_label: str = "primary"


@dataclass(slots=True)
class ImportExternalArtifactRequest:
    source_system: SourceSystem
    artifact_kind: ArtifactKind
    source_url: str | None = None
    observed_at: datetime | None = None
    external_case_id: UUID | None = None


class CourtIntelligenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = CourtIntelligenceRepository(session)
        self.audit = AuditRepository(session)
        self.jobs = JobRepository(session)
        self.fetch_agent = FetchAgent()
        self.extract_agent = ExtractAgent()
        self.normalize_agent = NormalizeAgent()
        self.party_resolution_agent = PartyResolutionAgent()
        self.quality_guard_agent = QualityGuardAgent()
        self.retrieval_agent = RetrievalAgent()
        self.memory_builder = MemoryArtifactBuilder()
        self.profile_agent = ProfileAgent()
        self.chronology_agent = ChronologyAgent()
        self.drafting_planner_agent = DraftingPlannerAgent()

    @staticmethod
    def _latest_timestamp(values: list[datetime]) -> datetime | None:
        normalized: list[datetime] = []
        for value in values:
            normalized.append(value if value.tzinfo is not None else value.replace(tzinfo=UTC))
        return max(normalized, default=None)

    async def link_external_case(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID,
        request: LinkExternalCaseRequest,
    ) -> ExternalCase:
        matter = await self.repository.get_matter(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        if matter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

        existing_case = None
        if request.cnr_number:
            existing_case = await self.repository.find_external_case_by_identifier(
                organization_id=organization_id,
                identifier_type="cnr_number",
                identifier_value=request.cnr_number,
            )
        if existing_case is None:
            existing_case = await self.repository.find_external_case_by_identifier(
                organization_id=organization_id,
                identifier_type="case_number",
                identifier_value=request.case_number,
            )

        court = await self.repository.ensure_court(
            name=request.court_name,
            slug=self.normalize_agent.slugify_court(request.court_name),
        )
        if existing_case is None:
            existing_case = await self.repository.create_external_case(
                ExternalCase(
                    organization_id=organization_id,
                    court_id=court.id,
                    title=request.case_title,
                    case_number=request.case_number,
                    cnr_number=request.cnr_number,
                    source_system=request.source_system,
                    source_url=request.source_url,
                    observed_at=datetime.now(UTC),
                    fetched_at=datetime.now(UTC),
                    content_hash=hashlib.sha256(
                        f"{request.case_number}:{request.case_title}".encode()
                    ).hexdigest(),
                    parser_version="manual-link-v1",
                    confidence=ConfidenceBand.MEDIUM,
                    verification_status=VerificationStatus.IMPORTED,
                    last_synced_at=datetime.now(UTC),
                )
            )
        await self.repository.upsert_identifier(
            external_case_id=existing_case.id,
            identifier_type="case_number",
            identifier_value=request.case_number,
            is_primary=request.cnr_number is None,
        )
        if request.cnr_number:
            await self.repository.upsert_identifier(
                external_case_id=existing_case.id,
                identifier_type="cnr_number",
                identifier_value=request.cnr_number,
                is_primary=True,
            )

        await self.repository.link_matter_external_case(
            matter_id=matter_id,
            external_case_id=existing_case.id,
            linked_by_user_id=actor_user_id,
            relationship_label=request.relationship_label,
            is_primary=True,
        )
        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="external_case.linked",
            entity_type="external_case",
            entity_id=str(existing_case.id),
            detail=f"{existing_case.case_number} -> matter {matter.reference_code}",
        )
        await self.session.commit()
        return existing_case

    async def import_external_case_artifact(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID,
        file_name: str,
        content_type: str,
        payload: bytes,
        request: ImportExternalArtifactRequest,
    ) -> ExternalCase:
        matter = await self.repository.get_matter(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        if matter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

        fetched = self.fetch_agent.store_snapshot(
            organization_id=organization_id,
            uploaded_by_user_id=actor_user_id,
            source_system=request.source_system,
            artifact_kind=request.artifact_kind,
            file_name=file_name,
            content_type=content_type,
            payload=payload,
            source_url=request.source_url,
            observed_at=request.observed_at,
        )
        await self.repository.create_public_source_snapshot(fetched.snapshot)
        parser_run = await self.repository.create_parser_run(
            parser_run=self._build_parser_run(
                organization_id=organization_id,
                raw_snapshot_id=fetched.snapshot.id,
                parser_name=f"{request.source_system.value}.parser",
            )
        )

        imported = self.extract_agent.parse_snapshot(
            source_system=request.source_system,
            artifact_kind=request.artifact_kind,
            file_name=file_name,
            content_type=content_type,
            payload=payload,
            content_hash=fetched.content_hash,
            source_url=request.source_url,
            observed_at=request.observed_at,
        )
        parser_run.status = "succeeded"
        parser_run.extracted_record_count = (
            len(imported.events)
            + len(imported.filings)
            + len(imported.parties)
            + len(imported.counsels)
        )
        parser_run.completed_at = datetime.now(UTC)

        external_case = await self._normalize_imported_case(
            organization_id=organization_id,
            matter_id=matter_id,
            actor_user_id=actor_user_id,
            imported=imported,
            snapshot_id=fetched.snapshot.id,
            snapshot_storage_path=fetched.snapshot.storage_path,
            payload=payload,
            file_name=file_name,
            content_type=content_type,
            requested_external_case_id=request.external_case_id,
        )

        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="external_case.imported",
            entity_type="external_case",
            entity_id=str(external_case.id),
            detail=f"{request.source_system.value}:{request.artifact_kind.value}",
        )
        await self.session.commit()
        return external_case

    async def reimport_snapshot(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID | None,
        snapshot_id: UUID,
        external_case_id: UUID | None = None,
    ) -> ExternalCase:
        snapshot = await self.session.get(PublicSourceSnapshot, snapshot_id)
        if snapshot is None or snapshot.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Snapshot not found")
        resolved_actor_user_id = actor_user_id or snapshot.uploaded_by_user_id
        if resolved_actor_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Snapshot replay requires a recorded operator",
            )

        payload = LocalFilesystemStorage().read_bytes(snapshot.storage_path)
        imported = self.extract_agent.parse_snapshot(
            source_system=snapshot.source_system,
            artifact_kind=snapshot.artifact_kind,
            file_name=snapshot.original_file_name,
            content_type=snapshot.content_type,
            payload=payload,
            content_hash=snapshot.content_hash,
            source_url=snapshot.source_url,
            observed_at=snapshot.observed_at,
        )

        external_case = await self._normalize_imported_case(
            organization_id=organization_id,
            matter_id=matter_id,
            actor_user_id=resolved_actor_user_id,
            imported=imported,
            snapshot_id=snapshot.id,
            snapshot_storage_path=snapshot.storage_path,
            payload=payload,
            file_name=snapshot.original_file_name,
            content_type=snapshot.content_type,
            requested_external_case_id=external_case_id,
        )
        await self.session.commit()
        return external_case

    async def list_matter_external_cases(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> list[tuple[MatterExternalCaseLink, ExternalCase]]:
        rows = await self.repository.list_matter_external_cases(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        return [(row.link, row.external_case) for row in rows]

    async def get_party_memory(
        self,
        *,
        party_id: UUID,
        organization_id: UUID,
    ):
        snapshot = await self.repository.latest_litigant_memory(
            party_id=party_id,
            organization_id=organization_id,
        )
        if snapshot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Party memory not found")
        return snapshot

    async def refresh_party_memory(
        self,
        *,
        party_id: UUID,
        organization_id: UUID,
        generated_by_job_id: UUID | None = None,
    ):
        party_result = await self.session.execute(
            select(Party).where(Party.id == party_id, Party.organization_id == organization_id)
        )
        party = party_result.scalar_one_or_none()
        if party is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Party not found")

        case_parties = await self.repository.list_case_parties_for_party(
            party_id=party_id,
            organization_id=organization_id,
        )
        case_ids = [external_case.id for _, external_case in case_parties]
        counsels = await self.repository.list_counsels_for_party_cases(external_case_ids=case_ids)

        aliases = list(
            (
                await self.session.execute(
                    select(func.distinct(CaseParty.display_name)).where(CaseParty.party_id == party_id)
                )
            ).scalars()
        )
        sections: list[tuple[str, list[str]]] = []
        source_refs: list[dict[str, object]] = []
        if aliases:
            refs = [f"[party-alias:{alias}]" for alias in aliases]
            sections.append(
                (
                    "Canonical Identity",
                    [
                        self.quality_guard_agent.cited_line(
                            f"Canonical name: {party.canonical_name}. Aliases: {', '.join(sorted(set(aliases)))}.",
                            refs,
                        )
                    ],
                )
            )
            for alias in aliases:
                source_refs.append({"type": "party_alias", "label": alias})

        role_lines: list[str] = []
        counsel_lines: list[str] = []
        claims: list[str] = []
        defenses: list[str] = []
        deadline_lines: list[str] = []
        contradiction_lines: list[str] = []

        for case_party, external_case in case_parties:
            case_ref = f"[case:{external_case.case_number}]"
            role_lines.append(
                self.quality_guard_agent.cited_line(
                    f"{external_case.case_number} in {external_case.title}: role {case_party.role.value}.",
                    [case_ref],
                )
            )
            source_refs.append(
                {
                    "type": "case_party",
                    "external_case_id": str(external_case.id),
                    "case_number": external_case.case_number,
                    "role": case_party.role.value,
                }
            )
            filings = list(
                (
                    await self.session.execute(
                        select(CaseFiling)
                        .where(CaseFiling.external_case_id == external_case.id)
                        .order_by(CaseFiling.filing_date.asc(), CaseFiling.created_at.asc())
                    )
                ).scalars()
            )
            for filing in filings:
                if case_party.role in {PartyRole.PETITIONER, PartyRole.APPELLANT, PartyRole.APPLICANT}:
                    for relief in filing.reliefs_sought:
                        claims.append(
                            self.quality_guard_agent.cited_line(
                                f"{external_case.case_number}: sought {relief}.",
                                [case_ref, f"[filing:{filing.title}]"],
                            )
                        )
                    for assertion in filing.fact_assertions:
                        claims.append(
                            self.quality_guard_agent.cited_line(
                                f"{external_case.case_number}: asserted {assertion}.",
                                [case_ref, f"[filing:{filing.title}]"],
                            )
                        )
                if case_party.role in {PartyRole.RESPONDENT, PartyRole.DEFENDANT, PartyRole.APPELLEE}:
                    for denial in filing.denials:
                        defenses.append(
                            self.quality_guard_agent.cited_line(
                                f"{external_case.case_number}: denied {denial}.",
                                [case_ref, f"[filing:{filing.title}]"],
                            )
                        )
                if filing.admissions and filing.denials:
                    contradiction_lines.append(
                        self.quality_guard_agent.cited_line(
                            f"{external_case.case_number}: filing {filing.title} carries both admissions and denials that need review.",
                            [case_ref, f"[filing:{filing.title}]"],
                        )
                    )

            deadlines = list(
                (
                    await self.session.execute(
                        select(CaseDeadline).where(CaseDeadline.external_case_id == external_case.id)
                    )
                ).scalars()
            )
            for deadline in deadlines:
                deadline_lines.append(
                    self.quality_guard_agent.cited_line(
                        f"{external_case.case_number}: {deadline.title} due on {deadline.due_date.isoformat()}.",
                        [case_ref],
                    )
                )

        for counsel in counsels:
            counsel_lines.append(
                self.quality_guard_agent.cited_line(
                    f"{counsel.counsel_name} appeared for {counsel.side_label or 'an unspecified side'}.",
                    [f"[counsel:{counsel.counsel_name}]"],
                )
            )

        sections.extend(
            [
                ("Role History Across Cases", role_lines),
                ("Counsel History", counsel_lines),
                ("Recurring Claims", claims),
                ("Recurring Defenses", defenses),
                ("Open Deadlines", deadline_lines),
                ("Credibility And Consistency Notes", contradiction_lines),
            ]
        )

        storage_path, markdown_content = self.memory_builder.save_markdown(
            relative_path=f"memories/litigants/{party_id}.md",
            title=f"Litigant Memory - {party.canonical_name}",
            sections=sections,
        )
        snapshot = self.memory_builder.build_litigant_snapshot(
            organization_id=organization_id,
            party_id=party_id,
            storage_path=storage_path,
            markdown_content=markdown_content,
            source_refs=source_refs,
            generated_by_job_id=generated_by_job_id,
            confidence=ConfidenceBand.MEDIUM if len(case_parties) >= 2 else ConfidenceBand.LOW,
        )
        prompt_run = await self.jobs.add_prompt_run(
            organization_id=organization_id,
            job_id=generated_by_job_id,
            prompt_name="litigant_memory",
            prompt_version="v1",
            input_json={"party_id": str(party_id), "case_count": len(case_parties)},
            output_summary=f"Generated litigant memory for {party.canonical_name}",
        )
        await self.jobs.add_model_run(
            organization_id=organization_id,
            job_id=generated_by_job_id,
            prompt_run_id=prompt_run.id,
            adapter_kind="generation",
            provider_name="deterministic-local",
            model_name="template-markdown-v1",
            status="succeeded",
            request_json={"party_id": str(party_id)},
            response_json={"storage_path": storage_path},
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        await self.repository.save_litigant_memory(snapshot)
        await self.session.commit()
        return snapshot

    async def get_case_memory(
        self,
        *,
        external_case_id: UUID,
        organization_id: UUID,
    ) -> CaseMemorySnapshot:
        snapshot = await self.repository.latest_case_memory(
            external_case_id=external_case_id,
            organization_id=organization_id,
        )
        if snapshot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case memory not found")
        return snapshot

    async def refresh_case_memory(
        self,
        *,
        external_case_id: UUID,
        organization_id: UUID,
        matter_id: UUID | None = None,
        generated_by_job_id: UUID | None = None,
    ) -> CaseMemorySnapshot:
        context = await self.repository.load_case_context(
            external_case_id=external_case_id,
            organization_id=organization_id,
        )
        external_case = context.external_case
        parties = context.parties
        counsels = context.counsels
        events = context.events
        filings = context.filings
        deadlines = context.deadlines
        listings = context.listings
        artifacts = context.artifacts

        source_refs: list[dict[str, object]] = [
            {"type": "external_case", "case_number": external_case.case_number, "title": external_case.title}
        ]

        identifiers = [external_case.case_number]
        if external_case.cnr_number:
            identifiers.append(f"CNR {external_case.cnr_number}")
        if external_case.neutral_citation:
            identifiers.append(external_case.neutral_citation)

        sections: list[tuple[str, list[str]]] = [
            (
                "Case Identifiers",
                [
                    self.quality_guard_agent.cited_line(
                        f"{' | '.join(identifiers)} in {external_case.court.name if external_case.court else 'Unknown court'}.",
                        [f"[case:{external_case.case_number}]"],
                    )
                ],
            ),
            (
                "Court And Bench",
                [
                    self.quality_guard_agent.cited_line(
                        f"Court: {external_case.court.name if external_case.court else 'Unknown'}. Bench: {external_case.bench.label if external_case.bench else 'Unspecified'}. Judge: {external_case.current_judge.full_name if external_case.current_judge else 'Unspecified'}.",
                        [f"[case:{external_case.case_number}]"],
                    )
                ],
            ),
            (
                "Party Lineup",
                [
                    self.quality_guard_agent.cited_line(
                        f"{case_party.role.value.title()}: {case_party.display_name}.",
                        [f"[case-party:{case_party.display_name}]"],
                    )
                    for case_party in parties
                ],
            ),
            (
                "Counsel Lineup",
                [
                    self.quality_guard_agent.cited_line(
                        f"{counsel.counsel_name} for {counsel.side_label or 'an unspecified side'}.",
                        [f"[counsel:{counsel.counsel_name}]"],
                    )
                    for counsel in counsels
                ],
            ),
            (
                "Full Chronology",
                [
                    self.quality_guard_agent.cited_line(
                        f"{event.event_date.isoformat()}: {event.title} - {event.description}",
                        [f"[event:{event.title}]"],
                    )
                    for event in events
                ],
            ),
            (
                "Filings",
                [
                    self.quality_guard_agent.cited_line(
                        f"{filing.filing_type} by {filing.filing_side.value} on {filing.filing_date.isoformat() if filing.filing_date else 'unknown date'}: {filing.extracted_summary or filing.title}.",
                        [f"[filing:{filing.title}]"],
                    )
                    for filing in filings
                ],
            ),
            (
                "Order And Judgment History",
                [
                    self.quality_guard_agent.cited_line(
                        f"{artifact.artifact_kind.value.replace('_', ' ').title()}: {artifact.title}.",
                        [f"[artifact:{artifact.title}]"],
                    )
                    for artifact in artifacts
                    if artifact.artifact_kind in {ArtifactKind.ORDER, ArtifactKind.JUDGMENT}
                ],
            ),
            (
                "Open Deadlines",
                [
                    self.quality_guard_agent.cited_line(
                        f"{deadline.title} due on {deadline.due_date.isoformat()}.",
                        [f"[deadline:{deadline.title}]"],
                    )
                    for deadline in deadlines
                ],
            ),
            (
                "Latest Procedural Posture",
                [
                    self.quality_guard_agent.cited_line(
                        f"Status: {external_case.status_text or 'Unknown'}; next listing {external_case.next_listing_date.isoformat() if external_case.next_listing_date else 'not available'}.",
                        [f"[case:{external_case.case_number}]"],
                    )
                ],
            ),
            (
                "Next Actionable Step",
                self._build_case_next_steps(external_case, deadlines, listings, filings),
            ),
        ]

        storage_path, markdown_content = self.memory_builder.save_markdown(
            relative_path=f"memories/cases/{external_case_id}.md",
            title=f"Case Memory - {external_case.case_number}",
            sections=sections,
        )
        snapshot = self.memory_builder.build_case_snapshot(
            organization_id=organization_id,
            external_case_id=external_case_id,
            matter_id=matter_id,
            storage_path=storage_path,
            markdown_content=markdown_content,
            source_refs=source_refs,
            generated_by_job_id=generated_by_job_id,
            confidence=ConfidenceBand.MEDIUM if len(events) + len(filings) >= 4 else ConfidenceBand.LOW,
        )
        prompt_run = await self.jobs.add_prompt_run(
            organization_id=organization_id,
            job_id=generated_by_job_id,
            prompt_name="case_memory",
            prompt_version="v1",
            input_json={"external_case_id": str(external_case_id)},
            output_summary=f"Generated case memory for {external_case.case_number}",
        )
        plan = self.drafting_planner_agent.plan_from_case_memory(markdown_content)
        await self.jobs.add_model_run(
            organization_id=organization_id,
            job_id=generated_by_job_id,
            prompt_run_id=prompt_run.id,
            adapter_kind="generation",
            provider_name="deterministic-local",
            model_name="template-markdown-v1",
            status="succeeded",
            request_json={"external_case_id": str(external_case_id)},
            response_json={"storage_path": storage_path, "draft_plan": plan},
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        await self.repository.save_case_memory(snapshot)
        await self.session.commit()
        return snapshot

    async def get_judge_profile(
        self,
        *,
        judge_id: UUID,
        organization_id: UUID,
    ) -> JudgeProfileSnapshot:
        snapshot = await self.repository.latest_judge_profile(
            judge_id=judge_id,
            organization_id=organization_id,
        )
        if snapshot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge profile not found")
        return snapshot

    async def refresh_judge_profile(
        self,
        *,
        judge_id: UUID,
        organization_id: UUID,
        generated_by_job_id: UUID | None = None,
    ) -> JudgeProfileSnapshot:
        judge_model = await self.session.get(Judge, judge_id)
        if judge_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judge not found")

        judge_result = await self.session.execute(
            select(ExternalCase).where(
                ExternalCase.current_judge_id == judge_id,
                ExternalCase.organization_id == organization_id,
            )
        )
        cases = list(judge_result.scalars())
        judge_row = await self.session.execute(
            select(func.count(CaseListing.id)).where(
                CaseListing.judge_id == judge_id,
                CaseListing.organization_id == organization_id,
            )
        )
        hearing_load = int(judge_row.scalar_one())
        adjournments = int(
            (
                await self.session.execute(
                    select(func.count(CaseEvent.id)).where(
                        CaseEvent.judge_id == judge_id,
                        CaseEvent.event_type == EventType.ADJOURNED,
                        CaseEvent.organization_id == organization_id,
                    )
                )
            ).scalar_one()
        )
        orders = int(
            (
                await self.session.execute(
                    select(func.count(CaseEvent.id)).where(
                        CaseEvent.judge_id == judge_id,
                        CaseEvent.event_type == EventType.ORDER_UPLOADED,
                        CaseEvent.organization_id == organization_id,
                    )
                )
            ).scalar_one()
        )
        judge_name = judge_model.full_name
        court_id = cases[0].court_id if cases else None

        sample_size = max(len(cases), 1)
        metrics: dict[str, object] = {
            "sample_size": sample_size,
            "hearing_load": hearing_load,
            "adjournment_share": round(adjournments / hearing_load, 2) if hearing_load else None,
            "interim_order_frequency": round(orders / hearing_load, 2) if hearing_load else None,
            "recent_cause_list_density": hearing_load,
        }
        sections = [
            (
                "Judge Profile",
                [
                    f"- Descriptive operational profile for {judge_name}. Sources: "
                    + ", ".join(f"[case:{case.case_number}]" for case in cases[:5])
                ],
            ),
            ("Recent Procedural Tendencies", self.profile_agent.metrics_markdown(metrics)),
        ]
        storage_path, markdown_content = self.memory_builder.save_markdown(
            relative_path=f"memories/judges/{judge_id}.md",
            title=f"Judge Profile - {judge_name}",
            sections=sections,
        )
        snapshot = self.memory_builder.build_judge_profile(
            organization_id=organization_id,
            judge_id=judge_id,
            court_id=court_id,
            storage_path=storage_path,
            markdown_content=markdown_content,
            source_refs=[{"type": "external_case", "case_number": case.case_number} for case in cases],
            generated_by_job_id=generated_by_job_id,
            sample_size=sample_size,
            freshness_timestamp=self._latest_timestamp([case.updated_at for case in cases]),
            metrics=metrics,
        )
        await self.repository.save_judge_profile(snapshot)
        await self.session.commit()
        return snapshot

    async def get_court_profile(
        self,
        *,
        court_id: UUID,
        organization_id: UUID,
    ) -> CourtProfileSnapshot:
        snapshot = await self.repository.latest_court_profile(
            court_id=court_id,
            organization_id=organization_id,
        )
        if snapshot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court profile not found")
        return snapshot

    async def refresh_court_profile(
        self,
        *,
        court_id: UUID,
        organization_id: UUID,
        generated_by_job_id: UUID | None = None,
    ) -> CourtProfileSnapshot:
        cases_result = await self.session.execute(
            select(ExternalCase).where(
                ExternalCase.court_id == court_id,
                ExternalCase.organization_id == organization_id,
            )
        )
        cases = list(cases_result.scalars())
        sample_size = len(cases)
        listings = int(
            (
                await self.session.execute(
                    select(func.count(CaseListing.id))
                    .join(ExternalCase, ExternalCase.id == CaseListing.external_case_id)
                    .where(
                        CaseListing.organization_id == organization_id,
                        ExternalCase.court_id == court_id,
                    )
                )
            ).scalar_one()
        )
        orders = int(
            (
                await self.session.execute(
                    select(func.count(CaseEvent.id))
                    .join(ExternalCase, ExternalCase.id == CaseEvent.external_case_id)
                    .where(
                        CaseEvent.organization_id == organization_id,
                        CaseEvent.event_type == EventType.ORDER_UPLOADED,
                        ExternalCase.court_id == court_id,
                    )
                )
            ).scalar_one()
        )
        metrics: dict[str, object] = {
            "sample_size": sample_size,
            "listing_depth": listings,
            "order_upload_lag_proxy": round(orders / sample_size, 2) if sample_size else None,
            "pendency_context": sample_size,
        }
        court = cases[0].court if cases and cases[0].court is not None else None
        court_name = court.name if court is not None else "Imported court"
        sections = [
            (
                "Court Profile",
                [
                    f"- Descriptive operational profile for {court_name}. Sources: "
                    + ", ".join(f"[case:{case.case_number}]" for case in cases[:5])
                ],
            ),
            ("Recent Procedural Tendencies", self.profile_agent.metrics_markdown(metrics)),
        ]
        storage_path, markdown_content = self.memory_builder.save_markdown(
            relative_path=f"memories/courts/{court_id}.md",
            title=f"Court Profile - {court_name}",
            sections=sections,
        )
        snapshot = self.memory_builder.build_court_profile(
            organization_id=organization_id,
            court_id=court_id,
            storage_path=storage_path,
            markdown_content=markdown_content,
            source_refs=[{"type": "external_case", "case_number": case.case_number} for case in cases],
            generated_by_job_id=generated_by_job_id,
            sample_size=sample_size,
            freshness_timestamp=self._latest_timestamp([case.updated_at for case in cases]),
            metrics=metrics,
        )
        await self.repository.save_court_profile(snapshot)
        await self.session.commit()
        return snapshot

    async def refresh_hybrid_index(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
        generated_by_job_id: UUID | None = None,
    ) -> int:
        linked_rows = await self.repository.list_matter_external_cases(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        documents = await self.repository.list_matter_documents(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        items: list[tuple[HybridEntityKind, str, str, str, str | None, dict[str, object], UUID | None, UUID | None, UUID | None, UUID | None]] = []
        for document in documents:
            if not document.extracted_text:
                continue
            items.append(
                (
                    HybridEntityKind.DOCUMENT,
                    str(document.id),
                    document.title,
                    document.extracted_text,
                    None,
                    {"source_url": document.source_url, "source_type": document.source_type.value},
                    None,
                    None,
                    None,
                    None,
                )
            )

        for row in linked_rows:
            external_case = row.external_case
            context = await self.repository.load_case_context(
                external_case_id=external_case.id,
                organization_id=organization_id,
            )
            for event in context.events:
                items.append(
                    (
                        HybridEntityKind.CASE_EVENT,
                        str(event.id),
                        f"{external_case.case_number} - {event.title}",
                        event.description,
                        event.source_anchor,
                        {"source_url": event.source_url, "event_type": event.event_type.value},
                        None,
                        event.judge_id,
                        external_case.court_id,
                        external_case.id,
                    )
                )
            for filing in context.filings:
                items.append(
                    (
                        HybridEntityKind.CASE_FILING,
                        str(filing.id),
                        filing.title,
                        filing.extracted_summary or " ".join(filing.fact_assertions + filing.denials),
                        None,
                        {"source_url": filing.source_url, "filing_type": filing.filing_type},
                        None,
                        None,
                        external_case.court_id,
                        external_case.id,
                    )
                )
            case_memory = await self.repository.latest_case_memory(
                external_case_id=external_case.id,
                organization_id=organization_id,
            )
            if case_memory is not None:
                items.append(
                    (
                        HybridEntityKind.CASE_MEMORY,
                        str(case_memory.id),
                        f"Case memory - {external_case.case_number}",
                        case_memory.markdown_content,
                        None,
                        {"source_url": None},
                        None,
                        external_case.current_judge_id,
                        external_case.court_id,
                        external_case.id,
                    )
                )

        entries = self.retrieval_agent.build_entries(
            organization_id=organization_id,
            matter_id=matter_id,
            external_case_id=None,
            items=items,
        )
        await self.repository.replace_hybrid_index_for_source_ids(
            organization_id=organization_id,
            entity_kind=HybridEntityKind.DOCUMENT,
            source_ids=[str(document.id) for document in documents if document.extracted_text],
        )
        for entity_kind in (HybridEntityKind.CASE_EVENT, HybridEntityKind.CASE_FILING, HybridEntityKind.CASE_MEMORY):
            await self.repository.replace_hybrid_index_for_source_ids(
                organization_id=organization_id,
                entity_kind=entity_kind,
                source_ids=[entry.source_id for entry in entries if entry.entity_kind == entity_kind],
            )
        await self.repository.add_hybrid_entries(entries)
        if generated_by_job_id is not None:
            await self.jobs.add_artifact(
                job_id=generated_by_job_id,
                artifact_type="hybrid_index_entries",
                artifact_id=str(len(entries)),
                label=f"{matter_id}",
            )
        await self.session.commit()
        return len(entries)

    async def search_hybrid(
        self,
        *,
        organization_id: UUID,
        query: str,
        matter_id: UUID | None,
        limit: int = 12,
    ) -> list[tuple[Document | None, str, HybridEntityKind, float, dict[str, object]]]:
        candidates = await self.repository.search_hybrid_entries(
            organization_id=organization_id,
            query=query,
            matter_id=matter_id,
            limit=limit,
        )
        scored = self.retrieval_agent.score(query=query, entries=candidates)
        results: list[tuple[Document | None, str, HybridEntityKind, float, dict[str, object]]] = []
        for entry, score in scored[:limit]:
            document = None
            if entry.entity_kind == HybridEntityKind.DOCUMENT:
                document = await self.session.get(Document, UUID(entry.source_id))
            results.append((document, entry.title, entry.entity_kind, score, entry.metadata_json))
        return results

    async def merged_chronology(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> list[dict[str, object]]:
        internal_events = await self.repository.load_matter_internal_chronology(matter_id=matter_id)
        linked_rows = await self.repository.list_matter_external_cases(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        merged: list[dict[str, object]] = [
            {
                "id": str(event.id),
                "event_date": event.event_date,
                "title": event.title,
                "description": event.summary,
                "source_kind": "internal_bundle",
                "source_label": event.title,
                "confidence": event.confidence,
            }
            for event in internal_events
        ]
        for row in linked_rows:
            context = await self.repository.load_case_context(
                external_case_id=row.external_case.id,
                organization_id=organization_id,
            )
            for event in context.events:
                merged.append(
                    {
                        "id": str(event.id),
                        "event_date": event.event_date,
                        "title": event.title,
                        "description": event.description,
                        "source_kind": "external_case_event",
                        "source_label": row.external_case.case_number,
                        "confidence": event.confidence.value,
                        "provenance": {
                            "source_system": event.source_system.value,
                            "verification_status": event.verification_status.value,
                        },
                    }
                )
            for listing in context.listings:
                merged.append(
                    {
                        "id": str(listing.id),
                        "event_date": listing.listing_date,
                        "title": "Listed",
                        "description": listing.purpose or "Case listed",
                        "source_kind": "external_listing",
                        "source_label": row.external_case.case_number,
                        "confidence": listing.confidence.value,
                        "provenance": {
                            "source_system": listing.source_system.value,
                            "verification_status": listing.verification_status.value,
                        },
                    }
                )
        merged.sort(
            key=lambda item: item["event_date"]
            if isinstance(item["event_date"], date)
            else date.min,
        )
        return merged

    async def hearing_delta(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> dict[str, object]:
        chronology = await self.merged_chronology(matter_id=matter_id, organization_id=organization_id)
        external_events = [item for item in chronology if item["source_kind"] != "internal_bundle"]
        return self.chronology_agent.summarize_hearing_delta(external_events)

    async def filing_lineage(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> list[dict[str, object]]:
        linked_rows = await self.repository.list_matter_external_cases(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        lineage: list[dict[str, object]] = []
        for row in linked_rows:
            filings = list(
                (
                    await self.session.execute(
                        select(CaseFiling)
                        .where(CaseFiling.external_case_id == row.external_case.id)
                        .order_by(CaseFiling.filing_date.asc(), CaseFiling.created_at.asc())
                    )
                ).scalars()
            )
            latest_by_side: dict[FilingSide, CaseFiling] = {}
            for filing in filings:
                previous = latest_by_side.get(filing.filing_side)
                delta = {
                    "new_fact_assertions": sorted(
                        set(filing.fact_assertions) - set(previous.fact_assertions if previous else [])
                    ),
                    "new_denials": sorted(
                        set(filing.denials) - set(previous.denials if previous else [])
                    ),
                }
                lineage.append(
                    {
                        "id": str(filing.id),
                        "external_case_id": str(row.external_case.id),
                        "case_number": row.external_case.case_number,
                        "filing_side": filing.filing_side.value,
                        "filing_type": filing.filing_type,
                        "title": filing.title,
                        "filing_date": filing.filing_date,
                        "reliefs_sought": filing.reliefs_sought,
                        "fact_assertions": filing.fact_assertions,
                        "admissions": filing.admissions,
                        "denials": filing.denials,
                        "annexures_relied": filing.annexures_relied,
                        "statutes_cited": filing.statutes_cited,
                        "precedents_cited": filing.precedents_cited,
                        "extracted_summary": filing.extracted_summary,
                        "delta": delta,
                    }
                )
                latest_by_side[filing.filing_side] = filing
        return lineage

    async def connected_matters(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID | None = None,
        external_case_id: UUID | None = None,
    ) -> list[ExternalCase]:
        return await self.repository.list_connected_matters(
            organization_id=organization_id,
            matter_id=matter_id,
            external_case_id=external_case_id,
        )

    def _build_parser_run(self, *, organization_id: UUID, raw_snapshot_id: UUID, parser_name: str):
        from app.domain.court_intelligence import ParserRun

        return ParserRun(
            organization_id=organization_id,
            raw_snapshot_id=raw_snapshot_id,
            parser_name=parser_name,
            parser_version="2026-04-07",
            status="running",
            started_at=datetime.now(UTC),
        )

    async def _normalize_imported_case(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID,
        imported: ImportedCaseData,
        snapshot_id: UUID,
        snapshot_storage_path: str,
        payload: bytes,
        file_name: str,
        content_type: str,
        requested_external_case_id: UUID | None,
    ) -> ExternalCase:
        court = await self.repository.ensure_court(
            name=imported.court_name,
            slug=self.normalize_agent.slugify_court(imported.court_name),
            court_type=imported.court_type,
            state_name=imported.state_name,
            city_name=imported.district_name,
        )
        establishment = None
        if imported.establishment_name:
            establishment = await self.repository.ensure_court_establishment(
                court_id=court.id,
                name=imported.establishment_name,
                code=imported.establishment_code,
                district_name=imported.district_name,
                state_name=imported.state_name,
            )
        bench = None
        if imported.bench_label:
            bench = await self.repository.ensure_bench(
                court_id=court.id,
                establishment_id=establishment.id if establishment else None,
                label=imported.bench_label,
                court_hall=imported.court_hall,
            )
        judge = None
        if imported.judge_name:
            normalized_judge_name = self.normalize_agent.normalize_name(imported.judge_name)
            judge = await self.repository.ensure_judge(
                full_name=imported.judge_name,
                normalized_name=normalized_judge_name,
            )
            await self.repository.ensure_judge_assignment(
                organization_id=organization_id,
                judge_id=judge.id,
                court_id=court.id,
                bench_id=bench.id if bench else None,
                role_title="Presiding Judge",
                source_system=imported.source_system,
                source_url=imported.source_url,
                raw_snapshot_id=snapshot_id,
                observed_at=imported.observed_at,
                fetched_at=imported.fetched_at,
                content_hash=imported.content_hash,
                parser_version=imported.parser_version,
                confidence=imported.confidence,
                verification_status=imported.verification_status,
            )

        external_case = None
        if requested_external_case_id is not None:
            external_case = await self.repository.get_external_case(
                external_case_id=requested_external_case_id,
                organization_id=organization_id,
            )
        if external_case is None and imported.cnr_number:
            external_case = await self.repository.find_external_case_by_identifier(
                organization_id=organization_id,
                identifier_type="cnr_number",
                identifier_value=imported.cnr_number,
            )
        if external_case is None:
            external_case = await self.repository.find_external_case_by_identifier(
                organization_id=organization_id,
                identifier_type="case_number",
                identifier_value=imported.case_number,
            )

        if external_case is None:
            external_case = await self.repository.create_external_case(
                ExternalCase(
                    organization_id=organization_id,
                    court_id=court.id,
                    establishment_id=establishment.id if establishment else None,
                    bench_id=bench.id if bench else None,
                    current_judge_id=judge.id if judge else None,
                    title=imported.title,
                    case_number=imported.case_number,
                    cnr_number=imported.cnr_number,
                    case_type=imported.case_type,
                    filing_number=imported.filing_number,
                    filing_date=imported.filing_date,
                    registration_date=imported.registration_date,
                    status_text=imported.status_text,
                    subject=imported.subject,
                    neutral_citation=imported.neutral_citation,
                    latest_stage=imported.latest_stage,
                    next_listing_date=imported.next_listing_date,
                    source_system=imported.source_system,
                    source_url=imported.source_url,
                    raw_snapshot_id=snapshot_id,
                    observed_at=imported.observed_at,
                    fetched_at=imported.fetched_at,
                    content_hash=imported.content_hash,
                    parser_version=imported.parser_version,
                    confidence=imported.confidence,
                    verification_status=imported.verification_status,
                    last_synced_at=datetime.now(UTC),
                )
            )
        else:
            external_case.court_id = court.id
            external_case.establishment_id = establishment.id if establishment else None
            external_case.bench_id = bench.id if bench else None
            external_case.current_judge_id = judge.id if judge else None
            external_case.title = imported.title
            external_case.case_number = imported.case_number
            external_case.cnr_number = imported.cnr_number
            external_case.case_type = imported.case_type
            external_case.filing_number = imported.filing_number
            external_case.filing_date = imported.filing_date
            external_case.registration_date = imported.registration_date
            external_case.status_text = imported.status_text
            external_case.subject = imported.subject
            external_case.neutral_citation = imported.neutral_citation
            external_case.latest_stage = imported.latest_stage
            external_case.next_listing_date = imported.next_listing_date
            external_case.source_system = imported.source_system
            external_case.source_url = imported.source_url
            external_case.raw_snapshot_id = snapshot_id
            external_case.observed_at = imported.observed_at
            external_case.fetched_at = imported.fetched_at
            external_case.content_hash = imported.content_hash
            external_case.parser_version = imported.parser_version
            external_case.confidence = imported.confidence
            external_case.verification_status = imported.verification_status
            external_case.last_synced_at = datetime.now(UTC)
            await self.session.flush()

        for identifier in imported.identifiers:
            await self.repository.upsert_identifier(
                external_case_id=external_case.id,
                identifier_type=identifier.identifier_type,
                identifier_value=identifier.identifier_value,
                is_primary=identifier.is_primary,
            )

        await self.repository.link_matter_external_case(
            matter_id=matter_id,
            external_case_id=external_case.id,
            linked_by_user_id=actor_user_id,
            relationship_label="primary",
            is_primary=True,
        )

        document = await IngestionService(self.session).ingest_bytes(
            payload=payload,
            file_name=file_name,
            content_type=content_type,
            metadata=IngestionMetadata(
                organization_id=organization_id,
                created_by_user_id=actor_user_id,
                matter_id=matter_id,
                source_type=DocumentSourceType.COURT_DOCUMENT,
                title=imported.title,
                authority_kind=(
                    AuthorityKind.JUDGMENT
                    if imported.artifact_kind in {ArtifactKind.ORDER, ArtifactKind.JUDGMENT}
                    else AuthorityKind.MATTER_DOCUMENT
                ),
                citation_text=imported.neutral_citation,
                court=imported.court_name,
                forum=imported.court_name,
                bench=imported.bench_label,
                decision_date=imported.filing_date or imported.registration_date,
                legal_issue=imported.subject,
                source_url=imported.source_url,
            ),
        )
        artifact_title = imported.artifacts[0].title if imported.artifacts else imported.title
        court_artifact = CourtArtifact(
            organization_id=organization_id,
            matter_id=matter_id,
            external_case_id=external_case.id,
            document_id=document.id,
            artifact_kind=imported.artifact_kind,
            title=artifact_title,
            file_name=file_name,
            content_type=content_type,
            storage_path=snapshot_storage_path,
            summary=imported.artifacts[0].summary if imported.artifacts else None,
            neutral_citation=imported.neutral_citation,
            source_system=imported.source_system,
            source_url=imported.source_url,
            raw_snapshot_id=snapshot_id,
            observed_at=imported.observed_at,
            fetched_at=imported.fetched_at,
            content_hash=imported.content_hash,
            parser_version=imported.parser_version,
            confidence=imported.confidence,
            verification_status=imported.verification_status,
        )
        self.session.add(court_artifact)
        await self.session.flush()

        if imported.artifact_kind == ArtifactKind.CASE_HISTORY:
            await self.repository.replace_case_parties(external_case_id=external_case.id)
            await self.repository.replace_case_counsels(external_case_id=external_case.id)
            await self.session.execute(delete(CaseEvent).where(CaseEvent.external_case_id == external_case.id))
            await self.session.execute(delete(CaseFiling).where(CaseFiling.external_case_id == external_case.id))
            await self.session.execute(delete(CaseDeadline).where(CaseDeadline.external_case_id == external_case.id))
        if imported.artifact_kind == ArtifactKind.CAUSE_LIST:
            await self.session.execute(delete(CaseListing).where(CaseListing.external_case_id == external_case.id))
            await self.session.execute(delete(CauseListEntry).where(CauseListEntry.external_case_id == external_case.id))

        for imported_party in imported.parties:
            normalized_name = self.party_resolution_agent.normalized_party_name(
                imported_party.display_name
            )
            party = await self.repository.ensure_party(
                organization_id=organization_id,
                canonical_name=imported_party.display_name,
                normalized_name=normalized_name,
            )
            for alias in imported_party.aliases:
                await self.repository.ensure_party_alias(
                    party_id=party.id,
                    alias=alias,
                    normalized_alias=self.party_resolution_agent.normalized_party_name(alias),
                )
            self.session.add(
                CaseParty(
                    external_case_id=external_case.id,
                    party_id=party.id,
                    role=imported_party.role,
                    display_name=imported_party.display_name,
                    side_label=imported_party.role.value,
                    source_system=imported.source_system,
                    source_url=imported.source_url,
                    raw_snapshot_id=snapshot_id,
                    observed_at=imported.observed_at,
                    fetched_at=imported.fetched_at,
                    content_hash=imported.content_hash,
                    parser_version=imported.parser_version,
                    confidence=imported.confidence,
                    verification_status=imported.verification_status,
                )
            )

        for imported_counsel in imported.counsels:
            counsel = CaseCounsel(
                external_case_id=external_case.id,
                party_id=None,
                counsel_name=imported_counsel.counsel_name,
                normalized_name=self.party_resolution_agent.normalized_party_name(
                    imported_counsel.counsel_name
                ),
                side_label=imported_counsel.side_label,
                source_system=imported.source_system,
                source_url=imported.source_url,
                raw_snapshot_id=snapshot_id,
                observed_at=imported.observed_at,
                fetched_at=imported.fetched_at,
                content_hash=imported.content_hash,
                parser_version=imported.parser_version,
                confidence=imported.confidence,
                verification_status=imported.verification_status,
            )
            self.session.add(counsel)
            await self.session.flush()
            for alias in imported_counsel.aliases:
                from app.domain.court_intelligence import CounselAlias

                self.session.add(
                    CounselAlias(
                        case_counsel_id=counsel.id,
                        alias=alias,
                        normalized_alias=self.party_resolution_agent.normalized_party_name(alias),
                    )
                )

        for imported_event in imported.events:
            event_judge_id = judge.id if judge and imported_event.judge_name == imported.judge_name else None
            self.session.add(
                CaseEvent(
                    organization_id=organization_id,
                    external_case_id=external_case.id,
                    court_artifact_id=court_artifact.id,
                    judge_id=event_judge_id,
                    event_type=imported_event.event_type,
                    event_date=imported_event.event_date,
                    title=imported_event.title,
                    description=imported_event.description,
                    source_anchor=imported_event.source_anchor,
                    is_latest_for_type=False,
                    source_system=imported.source_system,
                    source_url=imported.source_url,
                    raw_snapshot_id=snapshot_id,
                    observed_at=imported.observed_at,
                    fetched_at=imported.fetched_at,
                    content_hash=imported.content_hash,
                    parser_version=imported.parser_version,
                    confidence=imported.confidence,
                    verification_status=imported.verification_status,
                )
            )

        for imported_listing in imported.listings:
            listing = CaseListing(
                organization_id=organization_id,
                external_case_id=external_case.id,
                bench_id=bench.id if bench else None,
                judge_id=judge.id if judge else None,
                listing_date=imported_listing.listing_date,
                purpose=imported_listing.purpose,
                item_number=imported_listing.item_number,
                court_hall=imported_listing.court_hall,
                source_system=imported.source_system,
                source_url=imported.source_url,
                raw_snapshot_id=snapshot_id,
                observed_at=imported.observed_at,
                fetched_at=imported.fetched_at,
                content_hash=imported.content_hash,
                parser_version=imported.parser_version,
                confidence=imported.confidence,
                verification_status=imported.verification_status,
            )
            self.session.add(listing)
            await self.session.flush()
            self.session.add(
                CauseListEntry(
                    organization_id=organization_id,
                    external_case_id=external_case.id,
                    case_listing_id=listing.id,
                    court_artifact_id=court_artifact.id,
                    entry_text=imported_listing.purpose or "Cause list entry",
                    item_number=imported_listing.item_number,
                    source_system=imported.source_system,
                    source_url=imported.source_url,
                    raw_snapshot_id=snapshot_id,
                    observed_at=imported.observed_at,
                    fetched_at=imported.fetched_at,
                    content_hash=imported.content_hash,
                    parser_version=imported.parser_version,
                    confidence=imported.confidence,
                    verification_status=imported.verification_status,
                )
            )

        for imported_filing in imported.filings:
            self.session.add(
                CaseFiling(
                    organization_id=organization_id,
                    external_case_id=external_case.id,
                    court_artifact_id=court_artifact.id,
                    filing_side=imported_filing.filing_side,
                    filing_date=imported_filing.filing_date,
                    filing_type=imported_filing.filing_type,
                    title=imported_filing.title,
                    reliefs_sought=imported_filing.reliefs_sought,
                    fact_assertions=imported_filing.fact_assertions,
                    admissions=imported_filing.admissions,
                    denials=imported_filing.denials,
                    annexures_relied=imported_filing.annexures_relied,
                    statutes_cited=imported_filing.statutes_cited,
                    precedents_cited=imported_filing.precedents_cited,
                    extracted_summary=imported_filing.extracted_summary,
                    source_system=imported.source_system,
                    source_url=imported.source_url,
                    raw_snapshot_id=snapshot_id,
                    observed_at=imported.observed_at,
                    fetched_at=imported.fetched_at,
                    content_hash=imported.content_hash,
                    parser_version=imported.parser_version,
                    confidence=imported.confidence,
                    verification_status=imported.verification_status,
                )
            )

        for imported_deadline in imported.deadlines:
            self.session.add(
                CaseDeadline(
                    organization_id=organization_id,
                    external_case_id=external_case.id,
                    due_date=imported_deadline.due_date,
                    title=imported_deadline.title,
                    status_text=imported_deadline.status_text,
                    detail=imported_deadline.detail,
                    source_system=imported.source_system,
                    source_url=imported.source_url,
                    raw_snapshot_id=snapshot_id,
                    observed_at=imported.observed_at,
                    fetched_at=imported.fetched_at,
                    content_hash=imported.content_hash,
                    parser_version=imported.parser_version,
                    confidence=imported.confidence,
                    verification_status=imported.verification_status,
                )
            )

        for connected in imported.connected_cases:
            linked_case = await self.repository.find_external_case_by_identifier(
                organization_id=organization_id,
                identifier_type="case_number",
                identifier_value=connected.case_number,
            )
            if linked_case is None:
                linked_case = await self.repository.create_external_case(
                    ExternalCase(
                        organization_id=organization_id,
                        court_id=court.id,
                        title=connected.title,
                        case_number=connected.case_number,
                        source_system=imported.source_system,
                        source_url=imported.source_url,
                        raw_snapshot_id=snapshot_id,
                        observed_at=imported.observed_at,
                        fetched_at=imported.fetched_at,
                        content_hash=hashlib.sha256(
                            f"{connected.case_number}:{connected.title}".encode()
                        ).hexdigest(),
                        parser_version=imported.parser_version,
                        confidence=ConfidenceBand.LOW,
                        verification_status=VerificationStatus.NEEDS_REVIEW,
                        last_synced_at=datetime.now(UTC),
                    )
                )
                await self.repository.upsert_identifier(
                    external_case_id=linked_case.id,
                    identifier_type="case_number",
                    identifier_value=connected.case_number,
                )
            await self.repository.add_case_link(
                organization_id=organization_id,
                left_case_id=external_case.id,
                right_case_id=linked_case.id,
                relation_label=connected.relation_label,
                note=connected.note,
                source_system=imported.source_system,
                source_url=imported.source_url,
                raw_snapshot_id=snapshot_id,
                observed_at=imported.observed_at,
                fetched_at=imported.fetched_at,
                content_hash=imported.content_hash,
                parser_version=imported.parser_version,
                confidence=imported.confidence,
                verification_status=imported.verification_status,
            )

        await self.session.flush()

        for case_party in list(
            (
                await self.session.execute(
                    select(CaseParty).where(CaseParty.external_case_id == external_case.id)
                )
            ).scalars()
        ):
            await self.refresh_party_memory(
                party_id=case_party.party_id,
                organization_id=organization_id,
            )

        await self.refresh_case_memory(
            external_case_id=external_case.id,
            organization_id=organization_id,
            matter_id=matter_id,
        )
        if judge is not None:
            await self.refresh_judge_profile(judge_id=judge.id, organization_id=organization_id)
        await self.refresh_court_profile(court_id=court.id, organization_id=organization_id)
        await self.refresh_hybrid_index(matter_id=matter_id, organization_id=organization_id)
        return external_case

    @staticmethod
    def _build_case_next_steps(
        external_case: ExternalCase,
        deadlines: list[CaseDeadline],
        listings: list[CaseListing],
        filings: list[CaseFiling],
    ) -> list[str]:
        lines: list[str] = []
        if deadlines:
            soonest = min(deadlines, key=lambda item: item.due_date)
            lines.append(
                f"- Prioritize {soonest.title} before {soonest.due_date.isoformat()}. Sources: [deadline:{soonest.title}]"
            )
        elif external_case.next_listing_date:
            lines.append(
                f"- Prepare for the next listing on {external_case.next_listing_date.isoformat()}. Sources: [case:{external_case.case_number}]"
            )
        elif filings:
            latest = max(
                filings,
                key=lambda item: (item.filing_date or date.min, item.created_at),
            )
            lines.append(
                f"- Review follow-up work after {latest.title}. Sources: [filing:{latest.title}]"
            )
        if listings:
            latest_listing = max(listings, key=lambda item: item.listing_date)
            lines.append(
                f"- Track the cause list item {latest_listing.item_number or 'unavailable'} for the most recent listing. Sources: [listing:{latest_listing.listing_date.isoformat()}]"
            )
        return lines


async def read_upload_bytes(file: UploadFile) -> bytes:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    return payload
