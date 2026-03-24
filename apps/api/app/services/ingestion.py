from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.domain.document import Citation, Document, DocumentChunk, QuoteSpan
from app.domain.enums import AuthorityKind, DocumentSourceType, ProcessingStatus
from app.repositories.audit import AuditRepository
from app.repositories.bundle import BundleRepository
from app.services.bundle_analysis import BundleAnalysisService
from app.services.extraction import DocumentExtractor, ExtractedDocument
from app.services.quote_lock import QuoteLockService
from app.services.storage import LocalFilesystemStorage

logger = logging.getLogger(__name__)
UPLOAD_CHUNK_SIZE = 1024 * 1024
SAFE_FILE_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(slots=True)
class IngestionMetadata:
    organization_id: UUID
    created_by_user_id: UUID
    source_type: DocumentSourceType
    matter_id: UUID | None = None
    title: str | None = None
    authority_kind: AuthorityKind = AuthorityKind.MATTER_DOCUMENT
    citation_text: str | None = None
    court: str | None = None
    forum: str | None = None
    bench: str | None = None
    decision_date: date | None = None
    legal_issue: str | None = None
    source_url: str | None = None


async def process_document_job(
    *,
    document_id: UUID,
    organization_id: UUID,
) -> None:
    async with SessionLocal() as session:
        service = IngestionService(session)
        try:
            await service.process_document(
                document_id=document_id,
                organization_id=organization_id,
            )
        except Exception as exc:
            logger.exception("Background document processing failed for %s", document_id)
            await service.mark_document_failed(
                document_id=document_id,
                organization_id=organization_id,
                error=str(exc),
            )
            return


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.storage = LocalFilesystemStorage()
        self.extractor = DocumentExtractor()
        self.audit = AuditRepository(session)
        self.bundle_repository = BundleRepository(session)

    async def ingest_upload(self, *, file: UploadFile, metadata: IngestionMetadata) -> Document:
        payload = await self._read_upload_payload(file)
        file_name = self._safe_file_name(file.filename or f"upload-{uuid4()}")
        return await self.ingest_bytes(
            payload=payload,
            file_name=file_name,
            content_type=file.content_type or "application/octet-stream",
            metadata=metadata,
        )

    async def queue_upload(self, *, file: UploadFile, metadata: IngestionMetadata) -> Document:
        payload = await self._read_upload_payload(file)
        file_name = self._safe_file_name(file.filename or f"upload-{uuid4()}")
        return await self.queue_bytes(
            payload=payload,
            file_name=file_name,
            content_type=file.content_type or "application/octet-stream",
            metadata=metadata,
        )

    async def ingest_bytes(
        self,
        *,
        payload: bytes,
        file_name: str,
        content_type: str,
        metadata: IngestionMetadata,
    ) -> Document:
        document = await self._create_document_record(
            payload=payload,
            file_name=file_name,
            content_type=content_type,
            metadata=metadata,
        )
        return await self.process_document(
            document_id=document.id,
            organization_id=metadata.organization_id,
        )

    async def queue_bytes(
        self,
        *,
        payload: bytes,
        file_name: str,
        content_type: str,
        metadata: IngestionMetadata,
    ) -> Document:
        document = await self._create_document_record(
            payload=payload,
            file_name=file_name,
            content_type=content_type,
            metadata=metadata,
        )
        await self.audit.record(
            organization_id=metadata.organization_id,
            actor_user_id=metadata.created_by_user_id,
            action="document.queued",
            entity_type="document",
            entity_id=str(document.id),
            detail=f"{document.file_name} -> {document.source_type.value}",
        )
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def process_document(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
    ) -> Document:
        document = await self.bundle_repository.get_document(
            document_id=document_id,
            organization_id=organization_id,
        )
        if document is None:
            raise ValueError("Document not found for processing")

        document.processing_status = ProcessingStatus.PROCESSING
        document.processing_error = None
        document.processing_started_at = datetime.now(UTC)
        await self.session.flush()

        try:
            payload = self.storage.read_bytes(document.storage_path)
            extracted = self.extractor.extract(
                file_name=document.file_name,
                content_type=document.content_type,
                payload=payload,
            )
            await self._clear_document_derivatives(document.id)
            created_spans = await self._materialize_document(
                document=document,
                extracted=extracted,
            )
            document.processing_status = ProcessingStatus.READY
            document.processing_completed_at = datetime.now(UTC)
            document.processing_error = None

            bundle_analysis = BundleAnalysisService(self.session)
            await bundle_analysis.materialize_document_bundle(
                document=document,
                quote_spans=created_spans,
            )
            if document.matter_id is not None:
                await bundle_analysis.rebuild_matter_bundle(
                    matter_id=document.matter_id,
                    organization_id=document.organization_id,
                )

            await self.audit.record(
                organization_id=document.organization_id,
                actor_user_id=document.created_by_user_id,
                action="document.ingested",
                entity_type="document",
                entity_id=str(document.id),
                detail=f"{document.file_name} -> {document.source_type.value}",
            )
        except Exception as exc:
            document.processing_status = ProcessingStatus.FAILED
            document.processing_completed_at = datetime.now(UTC)
            document.processing_error = str(exc)
            await self.audit.record(
                organization_id=document.organization_id,
                actor_user_id=document.created_by_user_id,
                action="document.ingest_failed",
                entity_type="document",
                entity_id=str(document.id),
                detail=str(exc),
            )
            await self.session.commit()
            await self.session.refresh(document)
            raise

        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def mark_document_failed(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
        error: str,
    ) -> None:
        document = await self.bundle_repository.get_document(
            document_id=document_id,
            organization_id=organization_id,
        )
        if document is None:
            return
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = error[:4000]
        document.processing_completed_at = datetime.now(UTC)
        await self.session.commit()

    async def _create_document_record(
        self,
        *,
        payload: bytes,
        file_name: str,
        content_type: str,
        metadata: IngestionMetadata,
    ) -> Document:
        safe_file_name = self._safe_file_name(file_name)
        digest = hashlib.sha256(payload).hexdigest()
        storage_key = (
            f"{metadata.organization_id}/"
            f"{metadata.matter_id or 'public'}/"
            f"{digest}-{safe_file_name}"
        )
        stored = self.storage.save_bytes(storage_key, payload)
        document = Document(
            organization_id=metadata.organization_id,
            matter_id=metadata.matter_id,
            created_by_user_id=metadata.created_by_user_id,
            source_type=metadata.source_type,
            processing_status=ProcessingStatus.QUEUED,
            title=metadata.title or safe_file_name,
            file_name=safe_file_name,
            content_type=content_type,
            storage_path=stored.relative_path,
            sha256=digest,
            size_bytes=len(payload),
            authority_kind=metadata.authority_kind,
            citation_text=metadata.citation_text,
            court=metadata.court,
            forum=metadata.forum,
            bench=metadata.bench,
            decision_date=metadata.decision_date,
            legal_issue=metadata.legal_issue,
            source_url=metadata.source_url,
        )
        self.session.add(document)
        await self.session.flush()
        return document

    async def _read_upload_payload(self, file: UploadFile) -> bytes:
        total_size = 0
        chunks: list[bytes] = []
        while True:
            chunk = await file.read(UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > self.settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=(
                        "Upload exceeds the configured size limit of "
                        f"{self.settings.max_upload_size_bytes} bytes"
                    ),
                )
            chunks.append(chunk)
        await file.close()
        return b"".join(chunks)

    @staticmethod
    def _safe_file_name(file_name: str) -> str:
        candidate = Path(file_name).name.strip() or f"upload-{uuid4()}"
        sanitized = SAFE_FILE_NAME_PATTERN.sub("_", candidate)
        return sanitized[:255] or f"upload-{uuid4()}"

    async def _clear_document_derivatives(self, document_id: UUID) -> None:
        await self.bundle_repository.clear_document_artifacts(document_id)
        for model in (QuoteSpan, DocumentChunk, Citation):
            await self.session.execute(delete(model).where(model.document_id == document_id))

    async def _materialize_document(
        self,
        *,
        document: Document,
        extracted: ExtractedDocument,
    ) -> list[QuoteSpan]:
        document.title = document.title or extracted.title
        document.extracted_text = extracted.full_text
        document.extraction_method = extracted.extraction_method

        citation: Citation | None = None
        if document.citation_text:
            citation = Citation(
                document_id=document.id,
                citation_text=document.citation_text,
                authority_kind=document.authority_kind,
                court=document.court,
                forum=document.forum,
                bench=document.bench,
                decision_date=document.decision_date,
                legal_issue=document.legal_issue,
                source_url=document.source_url,
            )
            self.session.add(citation)
            await self.session.flush()

        created_spans: list[QuoteSpan] = []
        for index, paragraph in enumerate(extracted.paragraphs, start=1):
            chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                heading=paragraph.heading,
                text=paragraph.text,
                paragraph_start=paragraph.paragraph_number,
                paragraph_end=paragraph.paragraph_number,
                page_start=paragraph.page_number,
                page_end=paragraph.page_number,
            )
            self.session.add(chunk)

            anchor_label = (
                f"Page {paragraph.page_number}, paragraph {paragraph.paragraph_number}"
                if paragraph.page_number
                else f"Paragraph {paragraph.paragraph_number}"
            )
            span = QuoteSpan(
                document_id=document.id,
                citation_id=citation.id if citation else None,
                anchor_label=anchor_label,
                text=paragraph.text,
                checksum=QuoteLockService.checksum_for_text(paragraph.text),
                paragraph_start=paragraph.paragraph_number,
                paragraph_end=paragraph.paragraph_number,
                page_start=paragraph.page_number,
                page_end=paragraph.page_number,
            )
            self.session.add(span)
            created_spans.append(span)

        await self.session.flush()
        return created_spans
