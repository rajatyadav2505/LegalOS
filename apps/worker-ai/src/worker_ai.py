from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID

import app.db.models  # noqa: F401
from app.db.session import SessionLocal
from app.domain.enums import JobKind
from app.services.job_system import BoundedJobOrchestrator


async def run_job(job_id: UUID) -> dict[str, object]:
    async with SessionLocal() as session:
        orchestrator = BoundedJobOrchestrator(session)
        return await orchestrator.run_job(job_id=job_id)


async def run_next(worker_name: str) -> dict[str, object] | None:
    async with SessionLocal() as session:
        orchestrator = BoundedJobOrchestrator(session)
        return await orchestrator.run_next(worker_name=worker_name)


async def drain(limit: int, worker_name: str) -> dict[str, object]:
    processed = 0
    while processed < limit:
        result = await run_next(worker_name)
        if result is None:
            break
        processed += 1
    return {"processed": processed}


def load_payload(path: str) -> dict[str, object]:
    payload = json.loads(Path(path).read_text("utf-8"))
    if "kind" not in payload:
        raise ValueError("Job payload must include a kind")
    JobKind(payload["kind"])
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded court-intelligence jobs.")
    parser.add_argument("--job-id", help="Run a specific queued job by id.")
    parser.add_argument(
        "--run-next",
        action="store_true",
        help="Claim and run the next available job.",
    )
    parser.add_argument(
        "--drain",
        action="store_true",
        help="Drain a batch of queued jobs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of jobs to drain.",
    )
    parser.add_argument(
        "--worker-name",
        default="worker-ai",
        help="Worker identity recorded in the jobs table.",
    )
    args = parser.parse_args()

    if args.job_id:
        result = asyncio.run(run_job(UUID(args.job_id)))
        print(json.dumps(result, indent=2, default=str))
        return

    if args.run_next:
        result = asyncio.run(run_next(args.worker_name))
        print(json.dumps(result or {"status": "idle"}, indent=2, default=str))
        return

    if args.drain:
        result = asyncio.run(drain(args.limit, args.worker_name))
        print(json.dumps(result, indent=2, default=str))
        return

    raise SystemExit("Provide --job-id, --run-next, or --drain.")


if __name__ == "__main__":
    main()
