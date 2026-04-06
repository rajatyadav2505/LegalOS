from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.bundle import ChronologyEvent
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
    PublicSourceSnapshot,
    RegistryEvent,
)
from app.domain.document import Document
from app.domain.matter import Matter


@dataclass(slots=True)
class MatterLinkedExternalCaseRow:
    link: MatterExternalCaseLink
    external_case: ExternalCase


@dataclass(slots=True)
class ExternalCaseContext:
    external_case: ExternalCase
    parties: list[CaseParty]
    counsels: list[CaseCounsel]
    events: list[CaseEvent]
    filings: list[CaseFiling]
    listings: list[CaseListing]
    deadlines: list[CaseDeadline]
    artifacts: list[CourtArtifact]


class CourtIntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_matter(self, *, matter_id: UUID, organization_id: UUID) -> Matter | None:
        result = await self.session.execute(
            select(Matter).where(
                Matter.id == matter_id,
                Matter.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_external_case(
        self,
        *,
        external_case_id: UUID,
        organization_id: UUID,
    ) -> ExternalCase | None:
        result = await self.session.execute(
            select(ExternalCase)
            .where(
                ExternalCase.id == external_case_id,
                ExternalCase.organization_id == organization_id,
            )
            .options(
                selectinload(ExternalCase.court),
                selectinload(ExternalCase.establishment),
                selectinload(ExternalCase.bench),
                selectinload(ExternalCase.current_judge),
            )
        )
        return result.scalar_one_or_none()

    async def find_external_case_by_identifier(
        self,
        *,
        organization_id: UUID,
        identifier_type: str,
        identifier_value: str,
    ) -> ExternalCase | None:
        result = await self.session.execute(
            select(ExternalCase)
            .join(
                ExternalCaseIdentifier,
                ExternalCaseIdentifier.external_case_id == ExternalCase.id,
            )
            .where(
                ExternalCase.organization_id == organization_id,
                ExternalCaseIdentifier.identifier_type == identifier_type,
                ExternalCaseIdentifier.identifier_value == identifier_value,
            )
        )
        return result.scalar_one_or_none()

    async def list_matter_external_cases(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> list[MatterLinkedExternalCaseRow]:
        result = await self.session.execute(
            select(MatterExternalCaseLink, ExternalCase)
            .join(ExternalCase, ExternalCase.id == MatterExternalCaseLink.external_case_id)
            .join(Matter, Matter.id == MatterExternalCaseLink.matter_id)
            .where(
                MatterExternalCaseLink.matter_id == matter_id,
                Matter.organization_id == organization_id,
            )
            .options(
                selectinload(ExternalCase.court),
                selectinload(ExternalCase.bench),
                selectinload(ExternalCase.current_judge),
            )
            .order_by(MatterExternalCaseLink.is_primary.desc(), ExternalCase.updated_at.desc())
        )
        return [
            MatterLinkedExternalCaseRow(link=row[0], external_case=row[1])
            for row in result.all()
        ]

    async def ensure_court(
        self,
        *,
        name: str,
        slug: str,
        court_type: str | None = None,
        state_name: str | None = None,
        city_name: str | None = None,
    ) -> Court:
        result = await self.session.execute(select(Court).where(Court.slug == slug))
        court = result.scalar_one_or_none()
        if court is None:
            court = Court(
                name=name,
                slug=slug,
                court_type=court_type,
                state_name=state_name,
                city_name=city_name,
            )
            self.session.add(court)
            await self.session.flush()
            return court
        court.name = name
        court.court_type = court_type
        court.state_name = state_name
        court.city_name = city_name
        await self.session.flush()
        return court

    async def ensure_court_establishment(
        self,
        *,
        court_id: UUID,
        name: str,
        code: str | None,
        district_name: str | None = None,
        state_name: str | None = None,
    ) -> CourtEstablishment:
        result = await self.session.execute(
            select(CourtEstablishment).where(
                CourtEstablishment.court_id == court_id,
                CourtEstablishment.name == name,
            )
        )
        establishment = result.scalar_one_or_none()
        if establishment is None:
            establishment = CourtEstablishment(
                court_id=court_id,
                name=name,
                code=code,
                district_name=district_name,
                state_name=state_name,
            )
            self.session.add(establishment)
            await self.session.flush()
            return establishment
        establishment.code = code
        establishment.district_name = district_name
        establishment.state_name = state_name
        await self.session.flush()
        return establishment

    async def ensure_bench(
        self,
        *,
        court_id: UUID,
        establishment_id: UUID | None,
        label: str,
        bench_code: str | None = None,
        court_hall: str | None = None,
    ) -> Bench:
        result = await self.session.execute(
            select(Bench).where(Bench.court_id == court_id, Bench.label == label)
        )
        bench = result.scalar_one_or_none()
        if bench is None:
            bench = Bench(
                court_id=court_id,
                establishment_id=establishment_id,
                label=label,
                bench_code=bench_code,
                court_hall=court_hall,
            )
            self.session.add(bench)
            await self.session.flush()
            return bench
        bench.establishment_id = establishment_id
        bench.bench_code = bench_code
        bench.court_hall = court_hall
        await self.session.flush()
        return bench

    async def ensure_judge(
        self,
        *,
        full_name: str,
        normalized_name: str,
        honorific: str | None = None,
    ) -> Judge:
        result = await self.session.execute(
            select(Judge).where(Judge.normalized_name == normalized_name)
        )
        judge = result.scalar_one_or_none()
        if judge is None:
            judge = Judge(
                full_name=full_name,
                normalized_name=normalized_name,
                honorific=honorific,
            )
            self.session.add(judge)
            await self.session.flush()
            return judge
        judge.full_name = full_name
        judge.honorific = honorific
        await self.session.flush()
        return judge

    async def ensure_judge_assignment(
        self,
        *,
        organization_id: UUID,
        judge_id: UUID,
        court_id: UUID,
        bench_id: UUID | None,
        role_title: str | None,
        source_system,
        source_url: str | None,
        raw_snapshot_id: UUID | None,
        observed_at,
        fetched_at,
        content_hash: str | None,
        parser_version: str | None,
        confidence,
        verification_status,
    ) -> JudgeAssignment:
        result = await self.session.execute(
            select(JudgeAssignment).where(
                JudgeAssignment.organization_id == organization_id,
                JudgeAssignment.judge_id == judge_id,
                JudgeAssignment.court_id == court_id,
                JudgeAssignment.bench_id == bench_id,
            )
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            assignment = JudgeAssignment(
                organization_id=organization_id,
                judge_id=judge_id,
                court_id=court_id,
                bench_id=bench_id,
                role_title=role_title,
                source_system=source_system,
                source_url=source_url,
                raw_snapshot_id=raw_snapshot_id,
                observed_at=observed_at,
                fetched_at=fetched_at,
                content_hash=content_hash,
                parser_version=parser_version,
                confidence=confidence,
                verification_status=verification_status,
            )
            self.session.add(assignment)
            await self.session.flush()
            return assignment
        assignment.role_title = role_title
        assignment.source_system = source_system
        assignment.source_url = source_url
        assignment.raw_snapshot_id = raw_snapshot_id
        assignment.observed_at = observed_at
        assignment.fetched_at = fetched_at
        assignment.content_hash = content_hash
        assignment.parser_version = parser_version
        assignment.confidence = confidence
        assignment.verification_status = verification_status
        await self.session.flush()
        return assignment

    async def create_external_case(self, external_case: ExternalCase) -> ExternalCase:
        self.session.add(external_case)
        await self.session.flush()
        return external_case

    async def upsert_identifier(
        self,
        *,
        external_case_id: UUID,
        identifier_type: str,
        identifier_value: str,
        is_primary: bool = False,
    ) -> ExternalCaseIdentifier:
        result = await self.session.execute(
            select(ExternalCaseIdentifier).where(
                ExternalCaseIdentifier.external_case_id == external_case_id,
                ExternalCaseIdentifier.identifier_type == identifier_type,
                ExternalCaseIdentifier.identifier_value == identifier_value,
            )
        )
        identifier = result.scalar_one_or_none()
        if identifier is None:
            identifier = ExternalCaseIdentifier(
                external_case_id=external_case_id,
                identifier_type=identifier_type,
                identifier_value=identifier_value,
                is_primary=is_primary,
            )
            self.session.add(identifier)
            await self.session.flush()
            return identifier
        identifier.is_primary = is_primary
        await self.session.flush()
        return identifier

    async def link_matter_external_case(
        self,
        *,
        matter_id: UUID,
        external_case_id: UUID,
        linked_by_user_id: UUID,
        relationship_label: str,
        is_primary: bool,
    ) -> MatterExternalCaseLink:
        result = await self.session.execute(
            select(MatterExternalCaseLink).where(
                MatterExternalCaseLink.matter_id == matter_id,
                MatterExternalCaseLink.external_case_id == external_case_id,
            )
        )
        link = result.scalar_one_or_none()
        if link is None:
            link = MatterExternalCaseLink(
                matter_id=matter_id,
                external_case_id=external_case_id,
                linked_by_user_id=linked_by_user_id,
                relationship_label=relationship_label,
                is_primary=is_primary,
            )
            self.session.add(link)
            await self.session.flush()
            return link
        link.relationship_label = relationship_label
        link.is_primary = is_primary
        await self.session.flush()
        return link

    async def ensure_party(
        self,
        *,
        organization_id: UUID,
        canonical_name: str,
        normalized_name: str,
        party_type: str | None = None,
    ) -> Party:
        result = await self.session.execute(
            select(Party).where(
                Party.organization_id == organization_id,
                Party.normalized_name == normalized_name,
            )
        )
        party = result.scalar_one_or_none()
        if party is None:
            party = Party(
                organization_id=organization_id,
                canonical_name=canonical_name,
                normalized_name=normalized_name,
                party_type=party_type,
            )
            self.session.add(party)
            await self.session.flush()
            return party
        party.canonical_name = canonical_name
        party.party_type = party_type
        await self.session.flush()
        return party

    async def ensure_party_alias(self, *, party_id: UUID, alias: str, normalized_alias: str) -> PartyAlias:
        result = await self.session.execute(
            select(PartyAlias).where(
                PartyAlias.party_id == party_id,
                PartyAlias.normalized_alias == normalized_alias,
            )
        )
        party_alias = result.scalar_one_or_none()
        if party_alias is None:
            party_alias = PartyAlias(
                party_id=party_id,
                alias=alias,
                normalized_alias=normalized_alias,
            )
            self.session.add(party_alias)
            await self.session.flush()
            return party_alias
        party_alias.alias = alias
        await self.session.flush()
        return party_alias

    async def replace_case_parties(self, *, external_case_id: UUID) -> None:
        await self.session.execute(delete(CaseParty).where(CaseParty.external_case_id == external_case_id))

    async def replace_case_counsels(self, *, external_case_id: UUID) -> None:
        counsel_ids = list(
            (
                await self.session.execute(
                    select(CaseCounsel.id).where(CaseCounsel.external_case_id == external_case_id)
                )
            ).scalars()
        )
        if counsel_ids:
            await self.session.execute(delete(CounselAlias).where(CounselAlias.case_counsel_id.in_(counsel_ids)))
        await self.session.execute(delete(CaseCounsel).where(CaseCounsel.external_case_id == external_case_id))

    async def replace_case_docket(self, *, external_case_id: UUID) -> None:
        for model in (
            CauseListEntry,
            CaseListing,
            CaseDeadline,
            CaseEvent,
            CaseFiling,
            RegistryEvent,
            CaveatEntry,
            CourtArtifact,
        ):
            await self.session.execute(delete(model).where(model.external_case_id == external_case_id))

    async def add_case_link(
        self,
        *,
        organization_id: UUID,
        left_case_id: UUID,
        right_case_id: UUID,
        relation_label: str,
        note: str | None,
        source_system,
        source_url: str | None,
        raw_snapshot_id: UUID | None,
        observed_at,
        fetched_at,
        content_hash: str | None,
        parser_version: str | None,
        confidence,
        verification_status,
    ) -> ExternalCaseLink:
        relation = ExternalCaseLink(
            organization_id=organization_id,
            left_case_id=left_case_id,
            right_case_id=right_case_id,
            relation_label=relation_label,
            note=note,
            source_system=source_system,
            source_url=source_url,
            raw_snapshot_id=raw_snapshot_id,
            observed_at=observed_at,
            fetched_at=fetched_at,
            content_hash=content_hash,
            parser_version=parser_version,
            confidence=confidence,
            verification_status=verification_status,
        )
        self.session.add(relation)
        await self.session.flush()
        return relation

    async def create_public_source_snapshot(self, snapshot: PublicSourceSnapshot) -> PublicSourceSnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def create_parser_run(self, parser_run: ParserRun) -> ParserRun:
        self.session.add(parser_run)
        await self.session.flush()
        return parser_run

    async def latest_litigant_memory(
        self,
        *,
        party_id: UUID,
        organization_id: UUID,
    ) -> LitigantMemorySnapshot | None:
        result = await self.session.execute(
            select(LitigantMemorySnapshot)
            .where(
                LitigantMemorySnapshot.party_id == party_id,
                LitigantMemorySnapshot.organization_id == organization_id,
                LitigantMemorySnapshot.is_current.is_(True),
            )
            .order_by(LitigantMemorySnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save_litigant_memory(self, snapshot: LitigantMemorySnapshot) -> LitigantMemorySnapshot:
        await self.session.execute(
            delete(LitigantMemorySnapshot).where(
                LitigantMemorySnapshot.party_id == snapshot.party_id,
                LitigantMemorySnapshot.organization_id == snapshot.organization_id,
                LitigantMemorySnapshot.is_current.is_(True),
            )
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def latest_case_memory(
        self,
        *,
        external_case_id: UUID,
        organization_id: UUID,
    ) -> CaseMemorySnapshot | None:
        result = await self.session.execute(
            select(CaseMemorySnapshot)
            .where(
                CaseMemorySnapshot.external_case_id == external_case_id,
                CaseMemorySnapshot.organization_id == organization_id,
                CaseMemorySnapshot.is_current.is_(True),
            )
            .order_by(CaseMemorySnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save_case_memory(self, snapshot: CaseMemorySnapshot) -> CaseMemorySnapshot:
        await self.session.execute(
            delete(CaseMemorySnapshot).where(
                CaseMemorySnapshot.external_case_id == snapshot.external_case_id,
                CaseMemorySnapshot.organization_id == snapshot.organization_id,
                CaseMemorySnapshot.is_current.is_(True),
            )
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def latest_judge_profile(
        self,
        *,
        judge_id: UUID,
        organization_id: UUID,
    ) -> JudgeProfileSnapshot | None:
        result = await self.session.execute(
            select(JudgeProfileSnapshot)
            .where(
                JudgeProfileSnapshot.judge_id == judge_id,
                JudgeProfileSnapshot.organization_id == organization_id,
                JudgeProfileSnapshot.is_current.is_(True),
            )
            .order_by(JudgeProfileSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save_judge_profile(self, snapshot: JudgeProfileSnapshot) -> JudgeProfileSnapshot:
        await self.session.execute(
            delete(JudgeProfileSnapshot).where(
                JudgeProfileSnapshot.judge_id == snapshot.judge_id,
                JudgeProfileSnapshot.organization_id == snapshot.organization_id,
                JudgeProfileSnapshot.is_current.is_(True),
            )
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def latest_court_profile(
        self,
        *,
        court_id: UUID,
        organization_id: UUID,
    ) -> CourtProfileSnapshot | None:
        result = await self.session.execute(
            select(CourtProfileSnapshot)
            .where(
                CourtProfileSnapshot.court_id == court_id,
                CourtProfileSnapshot.organization_id == organization_id,
                CourtProfileSnapshot.is_current.is_(True),
            )
            .order_by(CourtProfileSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save_court_profile(self, snapshot: CourtProfileSnapshot) -> CourtProfileSnapshot:
        await self.session.execute(
            delete(CourtProfileSnapshot).where(
                CourtProfileSnapshot.court_id == snapshot.court_id,
                CourtProfileSnapshot.organization_id == snapshot.organization_id,
                CourtProfileSnapshot.is_current.is_(True),
            )
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def replace_hybrid_index_for_source_ids(
        self,
        *,
        organization_id: UUID,
        entity_kind,
        source_ids: Iterable[str],
    ) -> None:
        source_id_list = list(source_ids)
        if not source_id_list:
            return
        await self.session.execute(
            delete(HybridIndexEntry).where(
                HybridIndexEntry.organization_id == organization_id,
                HybridIndexEntry.entity_kind == entity_kind,
                HybridIndexEntry.source_id.in_(source_id_list),
            )
        )

    async def add_hybrid_entries(self, entries: Iterable[HybridIndexEntry]) -> None:
        self.session.add_all(list(entries))
        await self.session.flush()

    async def search_hybrid_entries(
        self,
        *,
        organization_id: UUID,
        query: str,
        matter_id: UUID | None,
        limit: int,
    ) -> list[HybridIndexEntry]:
        tokens = [token for token in re.findall(r"[A-Za-z0-9_]+", query.lower()) if len(token) >= 2]
        search_clauses = [
            or_(
                HybridIndexEntry.title.ilike(f"%{token}%"),
                HybridIndexEntry.body_text.ilike(f"%{token}%"),
            )
            for token in tokens
        ]
        if not search_clauses:
            search_clauses = [
                or_(
                    HybridIndexEntry.title.ilike(f"%{query}%"),
                    HybridIndexEntry.body_text.ilike(f"%{query}%"),
                )
            ]
        stmt = (
            select(HybridIndexEntry)
            .where(
                HybridIndexEntry.organization_id == organization_id,
                or_(*search_clauses),
            )
            .order_by(HybridIndexEntry.updated_at.desc())
            .limit(limit * 8)
        )
        if matter_id is not None:
            stmt = stmt.where(
                or_(
                    HybridIndexEntry.matter_id == matter_id,
                    HybridIndexEntry.matter_id.is_(None),
                )
            )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def load_case_context(
        self,
        *,
        external_case_id: UUID,
        organization_id: UUID,
    ) -> ExternalCaseContext:
        external_case = await self.get_external_case(
            external_case_id=external_case_id,
            organization_id=organization_id,
        )
        if external_case is None:
            raise ValueError("External case not found")

        parties = list(
            (
                await self.session.execute(
                    select(CaseParty)
                    .where(CaseParty.external_case_id == external_case_id)
                    .options(selectinload(CaseParty.party))
                )
            ).scalars()
        )
        counsels = list(
            (
                await self.session.execute(
                    select(CaseCounsel).where(CaseCounsel.external_case_id == external_case_id)
                )
            ).scalars()
        )
        events = list(
            (
                await self.session.execute(
                    select(CaseEvent)
                    .where(CaseEvent.external_case_id == external_case_id)
                    .order_by(CaseEvent.event_date.asc(), CaseEvent.created_at.asc())
                )
            ).scalars()
        )
        filings = list(
            (
                await self.session.execute(
                    select(CaseFiling)
                    .where(CaseFiling.external_case_id == external_case_id)
                    .order_by(CaseFiling.filing_date.asc(), CaseFiling.created_at.asc())
                )
            ).scalars()
        )
        listings = list(
            (
                await self.session.execute(
                    select(CaseListing)
                    .where(CaseListing.external_case_id == external_case_id)
                    .order_by(CaseListing.listing_date.asc(), CaseListing.created_at.asc())
                )
            ).scalars()
        )
        deadlines = list(
            (
                await self.session.execute(
                    select(CaseDeadline)
                    .where(CaseDeadline.external_case_id == external_case_id)
                    .order_by(CaseDeadline.due_date.asc())
                )
            ).scalars()
        )
        artifacts = list(
            (
                await self.session.execute(
                    select(CourtArtifact)
                    .where(CourtArtifact.external_case_id == external_case_id)
                    .order_by(CourtArtifact.created_at.desc())
                )
            ).scalars()
        )
        return ExternalCaseContext(
            external_case=external_case,
            parties=parties,
            counsels=counsels,
            events=events,
            filings=filings,
            listings=listings,
            deadlines=deadlines,
            artifacts=artifacts,
        )

    async def list_case_parties_for_party(
        self,
        *,
        party_id: UUID,
        organization_id: UUID,
    ) -> list[tuple[CaseParty, ExternalCase]]:
        result = await self.session.execute(
            select(CaseParty, ExternalCase)
            .join(ExternalCase, ExternalCase.id == CaseParty.external_case_id)
            .where(
                CaseParty.party_id == party_id,
                ExternalCase.organization_id == organization_id,
            )
            .order_by(ExternalCase.updated_at.desc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def list_counsels_for_party_cases(
        self,
        *,
        external_case_ids: Iterable[UUID],
    ) -> list[CaseCounsel]:
        case_ids = list(external_case_ids)
        if not case_ids:
            return []
        result = await self.session.execute(
            select(CaseCounsel).where(CaseCounsel.external_case_id.in_(case_ids))
        )
        return list(result.scalars())

    async def list_connected_matters(
        self,
        *,
        organization_id: UUID,
        external_case_id: UUID | None = None,
        matter_id: UUID | None = None,
        limit: int = 10,
    ) -> list[ExternalCase]:
        stmt = (
            select(ExternalCase)
            .where(ExternalCase.organization_id == organization_id)
            .options(selectinload(ExternalCase.court))
            .order_by(ExternalCase.updated_at.desc())
            .limit(limit)
        )
        if external_case_id is not None:
            stmt = stmt.where(ExternalCase.id != external_case_id)
        if matter_id is not None:
            linked_case_ids = list(
                (
                    await self.session.execute(
                        select(MatterExternalCaseLink.external_case_id).where(
                            MatterExternalCaseLink.matter_id == matter_id
                        )
                    )
                ).scalars()
            )
            if linked_case_ids:
                stmt = stmt.where(ExternalCase.id.not_in(linked_case_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def load_matter_internal_chronology(
        self,
        *,
        matter_id: UUID,
    ) -> list[ChronologyEvent]:
        result = await self.session.execute(
            select(ChronologyEvent)
            .where(ChronologyEvent.matter_id == matter_id)
            .order_by(ChronologyEvent.event_date.asc(), ChronologyEvent.created_at.asc())
        )
        return list(result.scalars())

    async def list_matter_documents(self, *, matter_id: UUID, organization_id: UUID) -> list[Document]:
        result = await self.session.execute(
            select(Document).where(
                Document.matter_id == matter_id,
                Document.organization_id == organization_id,
            )
        )
        return list(result.scalars())

    async def count_cases_for_judge(
        self,
        *,
        judge_id: UUID,
        organization_id: UUID,
    ) -> int:
        result = await self.session.execute(
            select(func.count(func.distinct(ExternalCase.id)))
            .outerjoin(CaseListing, CaseListing.external_case_id == ExternalCase.id)
            .outerjoin(CaseEvent, CaseEvent.external_case_id == ExternalCase.id)
            .where(
                ExternalCase.organization_id == organization_id,
                or_(ExternalCase.current_judge_id == judge_id, CaseListing.judge_id == judge_id, CaseEvent.judge_id == judge_id),
            )
        )
        return int(result.scalar_one())
