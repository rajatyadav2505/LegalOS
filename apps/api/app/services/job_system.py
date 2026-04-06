from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import JobKind, JobStatus
from app.repositories.audit import AuditRepository
from app.repositories.jobs import JobRepository
from app.services.court_intelligence import CourtIntelligenceService


class ExternalCaseSyncPayload(BaseModel):
    kind: Literal[JobKind.EXTERNAL_CASE_SYNC]
    matter_id: UUID
    external_case_id: UUID


class RawSnapshotImportPayload(BaseModel):
    kind: Literal[JobKind.RAW_SNAPSHOT_IMPORT]
    matter_id: UUID
    snapshot_id: UUID
    external_case_id: UUID | None = None


class ArtifactExtractPayload(BaseModel):
    kind: Literal[JobKind.ARTIFACT_EXTRACT]
    matter_id: UUID
    snapshot_id: UUID
    external_case_id: UUID | None = None


class CaseEventRebuildPayload(BaseModel):
    kind: Literal[JobKind.CASE_EVENT_REBUILD]
    matter_id: UUID
    external_case_id: UUID


class FilingParsePayload(BaseModel):
    kind: Literal[JobKind.FILING_PARSE]
    matter_id: UUID
    external_case_id: UUID


class PartyResolutionPayload(BaseModel):
    kind: Literal[JobKind.PARTY_RESOLUTION]
    matter_id: UUID
    external_case_id: UUID


class LitigantMemoryRefreshPayload(BaseModel):
    kind: Literal[JobKind.LITIGANT_MEMORY_REFRESH]
    party_id: UUID


class CaseMemoryRefreshPayload(BaseModel):
    kind: Literal[JobKind.CASE_MEMORY_REFRESH]
    matter_id: UUID | None = None
    external_case_id: UUID


class JudgeProfileRefreshPayload(BaseModel):
    kind: Literal[JobKind.JUDGE_PROFILE_REFRESH]
    judge_id: UUID


class CourtProfileRefreshPayload(BaseModel):
    kind: Literal[JobKind.COURT_PROFILE_REFRESH]
    court_id: UUID


class HybridIndexRefreshPayload(BaseModel):
    kind: Literal[JobKind.HYBRID_INDEX_REFRESH]
    matter_id: UUID


class HearingDeltaRefreshPayload(BaseModel):
    kind: Literal[JobKind.HEARING_DELTA_REFRESH]
    matter_id: UUID


JobPayload = (
    ExternalCaseSyncPayload
    | RawSnapshotImportPayload
    | ArtifactExtractPayload
    | CaseEventRebuildPayload
    | FilingParsePayload
    | PartyResolutionPayload
    | LitigantMemoryRefreshPayload
    | CaseMemoryRefreshPayload
    | JudgeProfileRefreshPayload
    | CourtProfileRefreshPayload
    | HybridIndexRefreshPayload
    | HearingDeltaRefreshPayload
)


class BoundedJobOrchestrator:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = JobRepository(session)
        self.audit = AuditRepository(session)
        self.service = CourtIntelligenceService(session)

    async def enqueue(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID | None,
        kind: JobKind,
        idempotency_key: str,
        payload: dict[str, object],
        matter_id: UUID | None = None,
        sensitive: bool = False,
    ):
        existing = await self.repository.get_by_idempotency_key(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            kind=kind,
        )
        if existing is not None:
            return existing

        job = await self.repository.create(
            organization_id=organization_id,
            matter_id=matter_id,
            actor_user_id=actor_user_id,
            kind=kind,
            payload_json=payload,
            idempotency_key=idempotency_key,
            sensitive=sensitive,
        )
        if sensitive:
            await self.audit.record(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action="job.enqueued",
                entity_type="job",
                entity_id=str(job.id),
                detail=kind.value,
            )
        await self.session.commit()
        return job

    async def run_job(self, *, job_id: UUID, worker_name: str = "worker-ai") -> dict[str, object]:
        job = await self.repository.get_by_id(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        if job.status == JobStatus.SUCCEEDED:
            return {"job_id": str(job.id), "status": "succeeded"}

        job.status = JobStatus.PENDING
        job.next_run_at = datetime.now(UTC)
        await self.session.flush()
        claimed = await self.repository.claim_next(worker_name=worker_name)
        if claimed is None:
            raise ValueError(f"Job {job_id} could not be claimed")
        if claimed.id != job.id:
            raise ValueError(f"Unexpected job claim order: expected {job_id}, got {claimed.id}")

        attempt = await self.repository.start_attempt(job=claimed)
        try:
            result = await self._dispatch(claimed)
        except Exception as exc:
            await self.repository.mark_failed(job=claimed, attempt=attempt, error_message=str(exc))
            if claimed.sensitive:
                await self.audit.record(
                    organization_id=claimed.organization_id,
                    actor_user_id=claimed.actor_user_id,
                    action="job.failed",
                    entity_type="job",
                    entity_id=str(claimed.id),
                    detail=str(exc),
                )
            await self.session.commit()
            raise

        await self.repository.mark_succeeded(job=claimed, attempt=attempt)
        if claimed.sensitive:
            await self.audit.record(
                organization_id=claimed.organization_id,
                actor_user_id=claimed.actor_user_id,
                action="job.succeeded",
                entity_type="job",
                entity_id=str(claimed.id),
                detail=claimed.kind.value,
            )
        await self.session.commit()
        return {"job_id": str(claimed.id), "status": "succeeded", "result": result}

    async def run_next(self, *, worker_name: str = "worker-ai") -> dict[str, object] | None:
        job = await self.repository.claim_next(worker_name=worker_name)
        if job is None:
            return None
        attempt = await self.repository.start_attempt(job=job)
        try:
            result = await self._dispatch(job)
        except Exception as exc:
            await self.repository.mark_failed(job=job, attempt=attempt, error_message=str(exc))
            await self.session.commit()
            raise
        await self.repository.mark_succeeded(job=job, attempt=attempt)
        await self.session.commit()
        return {"job_id": str(job.id), "status": "succeeded", "result": result}

    async def _dispatch(self, job) -> dict[str, object]:
        kind = job.kind
        payload = self._parse_payload(job.kind, job.payload_json)
        if kind == JobKind.EXTERNAL_CASE_SYNC:
            payload = ExternalCaseSyncPayload.model_validate(payload.model_dump())
            snapshot = await self.service.refresh_case_memory(
                external_case_id=payload.external_case_id,
                organization_id=job.organization_id,
                matter_id=payload.matter_id,
                generated_by_job_id=job.id,
            )
            await self.service.refresh_hybrid_index(
                matter_id=payload.matter_id,
                organization_id=job.organization_id,
                generated_by_job_id=job.id,
            )
            await self.repository.add_artifact(
                job_id=job.id,
                artifact_type="case_memory_snapshot",
                artifact_id=str(snapshot.id),
                label=str(payload.external_case_id),
            )
            return {"case_memory_snapshot_id": str(snapshot.id)}

        if kind in {JobKind.RAW_SNAPSHOT_IMPORT, JobKind.ARTIFACT_EXTRACT}:
            replay_payload = RawSnapshotImportPayload.model_validate(payload.model_dump())
            external_case = await self.service.reimport_snapshot(
                organization_id=job.organization_id,
                matter_id=replay_payload.matter_id,
                actor_user_id=job.actor_user_id,
                snapshot_id=replay_payload.snapshot_id,
                external_case_id=replay_payload.external_case_id,
            )
            await self.repository.add_artifact(
                job_id=job.id,
                artifact_type="external_case",
                artifact_id=str(external_case.id),
                label=external_case.case_number,
            )
            return {"external_case_id": str(external_case.id)}

        if kind == JobKind.CASE_EVENT_REBUILD:
            rebuild_payload = CaseEventRebuildPayload.model_validate(payload.model_dump())
            snapshot = await self.service.refresh_case_memory(
                external_case_id=rebuild_payload.external_case_id,
                organization_id=job.organization_id,
                matter_id=rebuild_payload.matter_id,
                generated_by_job_id=job.id,
            )
            return {"case_memory_snapshot_id": str(snapshot.id)}

        if kind == JobKind.FILING_PARSE:
            filing_payload = FilingParsePayload.model_validate(payload.model_dump())
            lineage = await self.service.filing_lineage(
                matter_id=filing_payload.matter_id,
                organization_id=job.organization_id,
            )
            await self.repository.add_artifact(
                job_id=job.id,
                artifact_type="filing_lineage",
                artifact_id=str(len(lineage)),
                label=str(filing_payload.external_case_id),
            )
            return {"filing_count": len(lineage)}

        if kind == JobKind.PARTY_RESOLUTION:
            party_payload = PartyResolutionPayload.model_validate(payload.model_dump())
            case_context = await self.service.repository.load_case_context(
                external_case_id=party_payload.external_case_id,
                organization_id=job.organization_id,
            )
            parties = case_context.parties
            generated = 0
            for case_party in parties:
                await self.service.refresh_party_memory(
                    party_id=case_party.party_id,
                    organization_id=job.organization_id,
                    generated_by_job_id=job.id,
                )
                generated += 1
            return {"party_memories_refreshed": generated}

        if kind == JobKind.LITIGANT_MEMORY_REFRESH:
            litigant_payload = LitigantMemoryRefreshPayload.model_validate(payload.model_dump())
            snapshot = await self.service.refresh_party_memory(
                party_id=litigant_payload.party_id,
                organization_id=job.organization_id,
                generated_by_job_id=job.id,
            )
            return {"litigant_memory_snapshot_id": str(snapshot.id)}

        if kind == JobKind.CASE_MEMORY_REFRESH:
            case_payload = CaseMemoryRefreshPayload.model_validate(payload.model_dump())
            snapshot = await self.service.refresh_case_memory(
                external_case_id=case_payload.external_case_id,
                organization_id=job.organization_id,
                matter_id=case_payload.matter_id,
                generated_by_job_id=job.id,
            )
            return {"case_memory_snapshot_id": str(snapshot.id)}

        if kind == JobKind.JUDGE_PROFILE_REFRESH:
            judge_payload = JudgeProfileRefreshPayload.model_validate(payload.model_dump())
            judge_snapshot = await self.service.refresh_judge_profile(
                judge_id=judge_payload.judge_id,
                organization_id=job.organization_id,
                generated_by_job_id=job.id,
            )
            return {"judge_profile_snapshot_id": str(judge_snapshot.id)}

        if kind == JobKind.COURT_PROFILE_REFRESH:
            court_payload = CourtProfileRefreshPayload.model_validate(payload.model_dump())
            court_snapshot = await self.service.refresh_court_profile(
                court_id=court_payload.court_id,
                organization_id=job.organization_id,
                generated_by_job_id=job.id,
            )
            return {"court_profile_snapshot_id": str(court_snapshot.id)}

        if kind == JobKind.HYBRID_INDEX_REFRESH:
            index_payload = HybridIndexRefreshPayload.model_validate(payload.model_dump())
            count = await self.service.refresh_hybrid_index(
                matter_id=index_payload.matter_id,
                organization_id=job.organization_id,
                generated_by_job_id=job.id,
            )
            return {"hybrid_index_count": count}

        if kind == JobKind.HEARING_DELTA_REFRESH:
            delta_payload = HearingDeltaRefreshPayload.model_validate(payload.model_dump())
            delta = await self.service.hearing_delta(
                matter_id=delta_payload.matter_id,
                organization_id=job.organization_id,
            )
            await self.repository.add_artifact(
                job_id=job.id,
                artifact_type="hearing_delta",
                artifact_id=str(delta_payload.matter_id),
                label=str(delta.get("latest_event_date")),
            )
            return delta

        raise ValueError(f"Unsupported job kind: {kind}")

    @staticmethod
    def _parse_payload(kind: JobKind, payload_json: dict[str, object]) -> JobPayload:
        payload_models: dict[JobKind, type[BaseModel]] = {
            JobKind.EXTERNAL_CASE_SYNC: ExternalCaseSyncPayload,
            JobKind.RAW_SNAPSHOT_IMPORT: RawSnapshotImportPayload,
            JobKind.ARTIFACT_EXTRACT: ArtifactExtractPayload,
            JobKind.CASE_EVENT_REBUILD: CaseEventRebuildPayload,
            JobKind.FILING_PARSE: FilingParsePayload,
            JobKind.PARTY_RESOLUTION: PartyResolutionPayload,
            JobKind.LITIGANT_MEMORY_REFRESH: LitigantMemoryRefreshPayload,
            JobKind.CASE_MEMORY_REFRESH: CaseMemoryRefreshPayload,
            JobKind.JUDGE_PROFILE_REFRESH: JudgeProfileRefreshPayload,
            JobKind.COURT_PROFILE_REFRESH: CourtProfileRefreshPayload,
            JobKind.HYBRID_INDEX_REFRESH: HybridIndexRefreshPayload,
            JobKind.HEARING_DELTA_REFRESH: HearingDeltaRefreshPayload,
        }
        model_type = payload_models[kind]
        return model_type.model_validate(payload_json)  # type: ignore[return-value]
