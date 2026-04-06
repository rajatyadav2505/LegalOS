from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.domain.court_intelligence import CaseParty, ExternalCase
from app.domain.enums import ArtifactKind, JobKind, SourceSystem
from app.repositories.jobs import JobRepository
from app.schemas.court_intelligence import (
    CasePartySummaryResponse,
    ConnectedMatterResponse,
    ExternalCaseLinkRequest,
    ExternalCaseSummaryResponse,
    FilingLineageItemResponse,
    HearingDeltaResponse,
    HybridSearchItemResponse,
    HybridSearchResponse,
    JobResponse,
    MatterExternalCaseListResponse,
    MemorySnapshotResponse,
    MergedChronologyItemResponse,
    ProfileSnapshotResponse,
    ProvenanceResponse,
)
from app.services.court_intelligence import (
    CourtIntelligenceService,
    ImportExternalArtifactRequest,
    LinkExternalCaseRequest,
    read_upload_bytes,
)
from app.services.job_system import BoundedJobOrchestrator

router = APIRouter()


def _build_provenance(entity) -> ProvenanceResponse:
    return ProvenanceResponse(
        source_system=entity.source_system,
        source_url=entity.source_url,
        raw_snapshot_id=entity.raw_snapshot_id,
        observed_at=entity.observed_at,
        fetched_at=entity.fetched_at,
        content_hash=entity.content_hash,
        parser_version=entity.parser_version,
        confidence=entity.confidence,
        verification_status=entity.verification_status,
    )


def _external_case_summary(external_case, *, matter_link=None) -> ExternalCaseSummaryResponse:
    return ExternalCaseSummaryResponse(
        id=external_case.id,
        matter_link_id=getattr(matter_link, "id", None),
        court_id=external_case.court_id,
        judge_id=external_case.current_judge_id,
        title=external_case.title,
        case_number=external_case.case_number,
        cnr_number=external_case.cnr_number,
        case_type=external_case.case_type,
        court_name=external_case.court.name if external_case.court else None,
        bench_label=external_case.bench.label if external_case.bench else None,
        judge_name=external_case.current_judge.full_name if external_case.current_judge else None,
        status_text=external_case.status_text,
        neutral_citation=external_case.neutral_citation,
        latest_stage=external_case.latest_stage,
        next_listing_date=external_case.next_listing_date,
        relationship_label=getattr(matter_link, "relationship_label", None),
        is_primary=getattr(matter_link, "is_primary", False),
        provenance=_build_provenance(external_case),
    )


def _job_response(job) -> JobResponse:
    return JobResponse(
        id=job.id,
        kind=job.kind,
        status=job.status,
        idempotency_key=job.idempotency_key,
        attempt_count=job.attempt_count,
        max_attempts=job.max_attempts,
        last_error=job.last_error,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


async def _enqueue_and_run(
    *,
    session: AsyncSession,
    organization_id: UUID,
    actor_user_id: UUID,
    kind: JobKind,
    idempotency_key: str,
    payload: dict[str, object],
    matter_id: UUID | None = None,
    sensitive: bool = True,
) -> JobResponse:
    orchestrator = BoundedJobOrchestrator(session)
    job = await orchestrator.enqueue(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        kind=kind,
        idempotency_key=idempotency_key,
        payload=payload,
        matter_id=matter_id,
        sensitive=sensitive,
    )
    await orchestrator.run_job(job_id=job.id)
    fresh_job = await JobRepository(session).get_by_id(job.id)
    assert fresh_job is not None
    return _job_response(fresh_job)


@router.post(
    "/matters/{matter_id}/external-cases/link",
    response_model=ExternalCaseSummaryResponse,
)
async def link_external_case(
    matter_id: UUID,
    request: ExternalCaseLinkRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExternalCaseSummaryResponse:
    service = CourtIntelligenceService(session)
    external_case = await service.link_external_case(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        actor_user_id=current_user.id,
        request=LinkExternalCaseRequest(**request.model_dump()),
    )
    return _external_case_summary(external_case)


@router.post(
    "/matters/{matter_id}/external-cases/import",
    response_model=ExternalCaseSummaryResponse,
)
async def import_external_case_artifact(
    matter_id: UUID,
    source_system: SourceSystem = Form(...),
    artifact_kind: ArtifactKind = Form(...),
    source_url: str | None = Form(default=None),
    observed_at: str | None = Form(default=None),
    external_case_id: UUID | None = Form(default=None),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ExternalCaseSummaryResponse:
    payload = await read_upload_bytes(file)
    service = CourtIntelligenceService(session)
    external_case = await service.import_external_case_artifact(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        actor_user_id=current_user.id,
        file_name=file.filename or "official-artifact",
        content_type=file.content_type or "application/octet-stream",
        payload=payload,
        request=ImportExternalArtifactRequest(
            source_system=source_system,
            artifact_kind=artifact_kind,
            source_url=source_url,
            observed_at=None if observed_at is None else datetime.fromisoformat(observed_at),
            external_case_id=external_case_id,
        ),
    )
    return _external_case_summary(external_case)


@router.get(
    "/matters/{matter_id}/external-cases",
    response_model=MatterExternalCaseListResponse,
)
async def list_external_cases(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> MatterExternalCaseListResponse:
    service = CourtIntelligenceService(session)
    rows = await service.list_matter_external_cases(
        matter_id=matter_id,
        organization_id=current_user.organization_id,
    )
    items = [
        _external_case_summary(external_case, matter_link=link) for link, external_case in rows
    ]
    return MatterExternalCaseListResponse(items=items, total=len(items))


@router.get(
    "/external-cases/{external_case_id}/parties",
    response_model=list[CasePartySummaryResponse],
)
async def list_external_case_parties(
    external_case_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[CasePartySummaryResponse]:
    result = await session.execute(
        select(CaseParty)
        .join(ExternalCase, ExternalCase.id == CaseParty.external_case_id)
        .where(
            CaseParty.external_case_id == external_case_id,
            ExternalCase.organization_id == current_user.organization_id,
        )
    )
    parties = list(result.scalars())
    return [
        CasePartySummaryResponse(
            party_id=party.party_id,
            display_name=party.display_name,
            role=party.role.value,
        )
        for party in parties
    ]


@router.post("/external-cases/{external_case_id}/sync", response_model=JobResponse)
async def sync_external_case(
    external_case_id: UUID,
    matter_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> JobResponse:
    service = CourtIntelligenceService(session)
    linked_cases = await service.list_matter_external_cases(
        matter_id=matter_id,
        organization_id=current_user.organization_id,
    )
    if not any(linked_case.id == external_case_id for _link, linked_case in linked_cases):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="External case is not linked to this matter",
        )
    return await _enqueue_and_run(
        session=session,
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        kind=JobKind.EXTERNAL_CASE_SYNC,
        idempotency_key=f"external-case-sync:{matter_id}:{external_case_id}",
        payload={
            "kind": JobKind.EXTERNAL_CASE_SYNC.value,
            "matter_id": str(matter_id),
            "external_case_id": str(external_case_id),
        },
        matter_id=matter_id,
    )


@router.get("/matters/{matter_id}/chronology", response_model=list[MergedChronologyItemResponse])
async def get_merged_chronology(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[MergedChronologyItemResponse]:
    service = CourtIntelligenceService(session)
    chronology = await service.merged_chronology(
        matter_id=matter_id,
        organization_id=current_user.organization_id,
    )
    return [MergedChronologyItemResponse.model_validate(item) for item in chronology]


@router.get("/matters/{matter_id}/hearing-delta", response_model=HearingDeltaResponse)
async def get_hearing_delta(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> HearingDeltaResponse:
    service = CourtIntelligenceService(session)
    delta = await service.hearing_delta(
        matter_id=matter_id,
        organization_id=current_user.organization_id,
    )
    return HearingDeltaResponse.model_validate(delta)


@router.get(
    "/matters/{matter_id}/filing-lineage",
    response_model=list[FilingLineageItemResponse],
)
async def get_filing_lineage(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[FilingLineageItemResponse]:
    service = CourtIntelligenceService(session)
    lineage = await service.filing_lineage(
        matter_id=matter_id,
        organization_id=current_user.organization_id,
    )
    return [FilingLineageItemResponse.model_validate(item) for item in lineage]


@router.get("/parties/{party_id}/memory", response_model=MemorySnapshotResponse)
async def get_party_memory(
    party_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> MemorySnapshotResponse:
    snapshot = await CourtIntelligenceService(session).get_party_memory(
        party_id=party_id,
        organization_id=current_user.organization_id,
    )
    return MemorySnapshotResponse.model_validate(snapshot, from_attributes=True)


@router.post("/parties/{party_id}/memory/refresh", response_model=JobResponse)
async def refresh_party_memory(
    party_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> JobResponse:
    return await _enqueue_and_run(
        session=session,
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        kind=JobKind.LITIGANT_MEMORY_REFRESH,
        idempotency_key=f"litigant-memory:{party_id}",
        payload={"kind": JobKind.LITIGANT_MEMORY_REFRESH.value, "party_id": str(party_id)},
    )


@router.get("/external-cases/{external_case_id}/memory", response_model=MemorySnapshotResponse)
async def get_case_memory(
    external_case_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> MemorySnapshotResponse:
    snapshot = await CourtIntelligenceService(session).get_case_memory(
        external_case_id=external_case_id,
        organization_id=current_user.organization_id,
    )
    return MemorySnapshotResponse.model_validate(snapshot, from_attributes=True)


@router.post("/external-cases/{external_case_id}/memory/refresh", response_model=JobResponse)
async def refresh_case_memory(
    external_case_id: UUID,
    matter_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> JobResponse:
    return await _enqueue_and_run(
        session=session,
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        kind=JobKind.CASE_MEMORY_REFRESH,
        idempotency_key=f"case-memory:{external_case_id}",
        payload={
            "kind": JobKind.CASE_MEMORY_REFRESH.value,
            "external_case_id": str(external_case_id),
            "matter_id": str(matter_id) if matter_id is not None else None,
        },
        matter_id=matter_id,
    )


@router.get("/judges/{judge_id}/profile", response_model=ProfileSnapshotResponse)
async def get_judge_profile(
    judge_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ProfileSnapshotResponse:
    snapshot = await CourtIntelligenceService(session).get_judge_profile(
        judge_id=judge_id,
        organization_id=current_user.organization_id,
    )
    return ProfileSnapshotResponse.model_validate(snapshot, from_attributes=True)


@router.post("/judges/{judge_id}/profile/refresh", response_model=JobResponse)
async def refresh_judge_profile(
    judge_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> JobResponse:
    return await _enqueue_and_run(
        session=session,
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        kind=JobKind.JUDGE_PROFILE_REFRESH,
        idempotency_key=f"judge-profile:{judge_id}",
        payload={"kind": JobKind.JUDGE_PROFILE_REFRESH.value, "judge_id": str(judge_id)},
    )


@router.get("/courts/{court_id}/profile", response_model=ProfileSnapshotResponse)
async def get_court_profile(
    court_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ProfileSnapshotResponse:
    snapshot = await CourtIntelligenceService(session).get_court_profile(
        court_id=court_id,
        organization_id=current_user.organization_id,
    )
    return ProfileSnapshotResponse.model_validate(snapshot, from_attributes=True)


@router.post("/courts/{court_id}/profile/refresh", response_model=JobResponse)
async def refresh_court_profile(
    court_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> JobResponse:
    return await _enqueue_and_run(
        session=session,
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        kind=JobKind.COURT_PROFILE_REFRESH,
        idempotency_key=f"court-profile:{court_id}",
        payload={"kind": JobKind.COURT_PROFILE_REFRESH.value, "court_id": str(court_id)},
    )


@router.get("/search/hybrid", response_model=HybridSearchResponse)
async def search_hybrid(
    q: str = Query(..., min_length=2),
    matter_id: UUID | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> HybridSearchResponse:
    items = await CourtIntelligenceService(session).search_hybrid(
        organization_id=current_user.organization_id,
        query=q,
        matter_id=matter_id,
        limit=limit,
    )
    response_items = [
        HybridSearchItemResponse(
            title=title,
            entity_kind=entity_kind,
            score=score,
            metadata=metadata,
        )
        for _document, title, entity_kind, score, metadata in items
    ]
    return HybridSearchResponse(items=response_items, total=len(response_items))


@router.get("/search/connected-matters", response_model=list[ConnectedMatterResponse])
async def get_connected_matters(
    matter_id: UUID | None = Query(default=None),
    external_case_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[ConnectedMatterResponse]:
    items = await CourtIntelligenceService(session).connected_matters(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        external_case_id=external_case_id,
    )
    return [
        ConnectedMatterResponse(
            id=item.id,
            title=item.title,
            case_number=item.case_number,
            cnr_number=item.cnr_number,
            court_name=item.court.name if item.court else None,
            next_listing_date=item.next_listing_date,
        )
        for item in items
    ]
