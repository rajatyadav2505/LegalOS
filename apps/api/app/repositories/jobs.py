from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import JobAttemptStatus, JobKind, JobStatus
from app.domain.jobs import Job, JobArtifact, JobAttempt, ModelRun, PromptRun


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, job_id: UUID) -> Job | None:
        result = await self.session.execute(
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.attempts))
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        *,
        organization_id: UUID,
        idempotency_key: str,
        kind: JobKind,
    ) -> Job | None:
        result = await self.session.execute(
            select(Job).where(
                Job.organization_id == organization_id,
                Job.idempotency_key == idempotency_key,
                Job.kind == kind,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID | None,
        actor_user_id: UUID | None,
        kind: JobKind,
        payload_json: dict[str, object],
        idempotency_key: str,
        sensitive: bool,
        max_attempts: int = 3,
    ) -> Job:
        job = Job(
            organization_id=organization_id,
            matter_id=matter_id,
            actor_user_id=actor_user_id,
            kind=kind,
            payload_json=payload_json,
            idempotency_key=idempotency_key,
            sensitive=sensitive,
            max_attempts=max_attempts,
            next_run_at=datetime.now(UTC),
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def claim_next(self, *, worker_name: str) -> Job | None:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(Job)
            .where(
                Job.status.in_((JobStatus.PENDING, JobStatus.RETRYABLE)),
                Job.next_run_at.is_not(None),
                Job.next_run_at <= now,
            )
            .order_by(Job.created_at.asc())
            .limit(1)
            .options(selectinload(Job.attempts))
        )
        job = result.scalar_one_or_none()
        if job is None:
            return None

        job.status = JobStatus.RUNNING
        job.locked_by = worker_name
        job.locked_at = now
        job.started_at = now
        job.attempt_count += 1
        await self.session.flush()
        return job

    async def start_attempt(self, *, job: Job) -> JobAttempt:
        attempt = JobAttempt(
            job_id=job.id,
            attempt_number=job.attempt_count,
            status=JobAttemptStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        self.session.add(attempt)
        await self.session.flush()
        return attempt

    async def mark_succeeded(self, *, job: Job, attempt: JobAttempt) -> None:
        now = datetime.now(UTC)
        attempt.status = JobAttemptStatus.SUCCEEDED
        attempt.completed_at = now
        job.status = JobStatus.SUCCEEDED
        job.completed_at = now
        job.last_error = None
        job.locked_at = None
        job.locked_by = None
        await self.session.flush()

    async def mark_failed(
        self,
        *,
        job: Job,
        attempt: JobAttempt,
        error_message: str,
        retry_delay_seconds: int = 30,
    ) -> None:
        now = datetime.now(UTC)
        attempt.status = JobAttemptStatus.FAILED
        attempt.error_message = error_message[:4000]
        attempt.completed_at = now
        job.last_error = error_message[:4000]
        job.locked_at = None
        job.locked_by = None
        if job.attempt_count >= job.max_attempts:
            job.status = JobStatus.FAILED
            job.completed_at = now
            job.next_run_at = None
        else:
            job.status = JobStatus.RETRYABLE
            job.next_run_at = now + timedelta(seconds=retry_delay_seconds)
        await self.session.flush()

    async def add_artifact(
        self,
        *,
        job_id: UUID,
        artifact_type: str,
        artifact_id: str,
        label: str | None = None,
    ) -> JobArtifact:
        artifact = JobArtifact(
            job_id=job_id,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            label=label,
        )
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def add_prompt_run(
        self,
        *,
        organization_id: UUID,
        job_id: UUID | None,
        prompt_name: str,
        prompt_version: str,
        input_json: dict[str, object],
        output_summary: str | None,
        privacy_mode: str = "redacted",
    ) -> PromptRun:
        prompt_run = PromptRun(
            organization_id=organization_id,
            job_id=job_id,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            input_json=input_json,
            output_summary=output_summary,
            privacy_mode=privacy_mode,
        )
        self.session.add(prompt_run)
        await self.session.flush()
        return prompt_run

    async def add_model_run(
        self,
        *,
        organization_id: UUID,
        job_id: UUID | None,
        prompt_run_id: UUID | None,
        adapter_kind: str,
        provider_name: str,
        model_name: str,
        status: str,
        request_json: dict[str, object],
        response_json: dict[str, object],
        started_at: datetime | None,
        completed_at: datetime | None,
    ) -> ModelRun:
        model_run = ModelRun(
            organization_id=organization_id,
            job_id=job_id,
            prompt_run_id=prompt_run_id,
            adapter_kind=adapter_kind,
            provider_name=provider_name,
            model_name=model_name,
            status=status,
            request_json=request_json,
            response_json=response_json,
            started_at=started_at,
            completed_at=completed_at,
        )
        self.session.add(model_run)
        await self.session.flush()
        return model_run
