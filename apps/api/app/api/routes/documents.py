from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.domain.document import Document
from app.domain.enums import AuthorityKind, DocumentSourceType, ProcessingStatus
from app.repositories.documents import DocumentRepository
from app.schemas.document import DocumentResponse
from app.services.ingestion import (
    IngestionMetadata,
    IngestionService,
    process_document_job,
)

router = APIRouter()


def _processing_stage(processing_status: ProcessingStatus) -> str:
    return {
        ProcessingStatus.QUEUED: "queued",
        ProcessingStatus.PROCESSING: "processing",
        ProcessingStatus.READY: "ready",
        ProcessingStatus.FAILED: "failed",
    }[processing_status]


def _processing_progress(processing_status: ProcessingStatus) -> int:
    return {
        ProcessingStatus.QUEUED: 5,
        ProcessingStatus.PROCESSING: 60,
        ProcessingStatus.READY: 100,
        ProcessingStatus.FAILED: 100,
    }[processing_status]


def _build_document_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        matter_id=document.matter_id,
        title=document.title,
        file_name=document.file_name,
        content_type=document.content_type,
        source_type=document.source_type,
        processing_status=document.processing_status,
        authority_kind=document.authority_kind,
        citation_text=document.citation_text,
        court=document.court,
        forum=document.forum,
        bench=document.bench,
        decision_date=document.decision_date,
        legal_issue=document.legal_issue,
        processing_stage=_processing_stage(document.processing_status),
        processing_progress=_processing_progress(document.processing_status),
        extraction_method=document.extraction_method,
        processing_error=document.processing_error,
        processing_started_at=document.processing_started_at,
        processing_completed_at=document.processing_completed_at,
        created_at=document.created_at,
    )


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    matter_id: UUID | None = Form(default=None),
    source_type: DocumentSourceType = Form(default=DocumentSourceType.MY_DOCUMENT),
    title: str | None = Form(default=None),
    authority_kind: AuthorityKind = Form(default=AuthorityKind.MATTER_DOCUMENT),
    citation_text: str | None = Form(default=None),
    court: str | None = Form(default=None),
    forum: str | None = Form(default=None),
    bench: str | None = Form(default=None),
    legal_issue: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    process_in_background: bool = Form(default=False),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> DocumentResponse:
    service = IngestionService(session)
    metadata = IngestionMetadata(
        organization_id=current_user.organization_id,
        created_by_user_id=current_user.id,
        matter_id=matter_id,
        source_type=source_type,
        title=title,
        authority_kind=authority_kind,
        citation_text=citation_text,
        court=court,
        forum=forum,
        bench=bench,
        legal_issue=legal_issue,
        source_url=source_url,
    )

    if process_in_background:
        document = await service.queue_upload(file=file, metadata=metadata)
        background_tasks.add_task(
            process_document_job,
            document_id=document.id,
            organization_id=current_user.organization_id,
        )
    else:
        document = await service.ingest_upload(file=file, metadata=metadata)

    return _build_document_response(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> DocumentResponse:
    document = await DocumentRepository(session).get_by_id(
        document_id=document_id,
        organization_id=current_user.organization_id,
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _build_document_response(document)
