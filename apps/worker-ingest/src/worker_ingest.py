from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID

from app.db.session import SessionLocal
from app.domain.document import Document
from app.domain.enums import AuthorityKind, DocumentSourceType, ProcessingStatus
from app.services.ingestion import IngestionMetadata, IngestionService
from pydantic import BaseModel
from sqlalchemy import select


class FilesystemIngestJob(BaseModel):
    organization_id: UUID
    created_by_user_id: UUID
    file_path: str
    content_type: str
    source_type: DocumentSourceType
    matter_id: UUID | None = None
    title: str | None = None
    authority_kind: AuthorityKind = AuthorityKind.MATTER_DOCUMENT
    citation_text: str | None = None
    court: str | None = None
    forum: str | None = None
    bench: str | None = None
    legal_issue: str | None = None
    source_url: str | None = None


async def run_job(job: FilesystemIngestJob) -> None:
    file_path = Path(job.file_path)
    async with SessionLocal() as session:
        service = IngestionService(session)
        await service.ingest_bytes(
            payload=file_path.read_bytes(),
            file_name=file_path.name,
            content_type=job.content_type,
            metadata=IngestionMetadata(
                organization_id=job.organization_id,
                created_by_user_id=job.created_by_user_id,
                source_type=job.source_type,
                matter_id=job.matter_id,
                title=job.title,
                authority_kind=job.authority_kind,
                citation_text=job.citation_text,
                court=job.court,
                forum=job.forum,
                bench=job.bench,
                legal_issue=job.legal_issue,
                source_url=job.source_url,
            ),
        )


async def process_document(document_id: UUID) -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Document.organization_id).where(Document.id == document_id)
        )
        organization_id = result.scalar_one_or_none()
        if organization_id is None:
            raise ValueError(f"Document {document_id} not found")
        await IngestionService(session).process_document(
            document_id=document_id,
            organization_id=organization_id,
        )


async def drain_queued(limit: int) -> int:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Document.id, Document.organization_id)
            .where(Document.processing_status == ProcessingStatus.QUEUED)
            .order_by(Document.created_at.asc())
            .limit(limit)
        )
        queued_rows = list(result.all())

    for document_id, _ in queued_rows:
        await process_document(document_id)

    return len(queued_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ingest jobs or drain queued documents.")
    parser.add_argument("job", nargs="?", help="Path to a JSON job envelope.")
    parser.add_argument("--document-id", help="Process a queued document by id.")
    parser.add_argument(
        "--drain-queued",
        action="store_true",
        help="Process queued documents from the database in created order.",
    )
    parser.add_argument("--limit", type=int, default=25, help="Maximum documents to drain.")
    args = parser.parse_args()

    if args.document_id:
        asyncio.run(process_document(UUID(args.document_id)))
        return

    if args.drain_queued:
        processed = asyncio.run(drain_queued(args.limit))
        print(json.dumps({"processed": processed}, indent=2))
        return

    if not args.job:
        raise SystemExit("Provide either a job path, --document-id, or --drain-queued.")

    job = FilesystemIngestJob.model_validate(json.loads(Path(args.job).read_text("utf-8")))
    asyncio.run(run_job(job))


if __name__ == "__main__":
    main()
