from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.schemas.drafting import (
    DraftDocumentResponse,
    DraftExportResponse,
    DraftGenerateRequest,
    DraftRedlineResponse,
    StylePackCreateRequest,
    StylePackResponse,
)
from app.services.drafting import DraftingService

router = APIRouter()


@router.get("/style-packs", response_model=list[StylePackResponse])
async def list_style_packs(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[StylePackResponse]:
    return await DraftingService(session).list_style_packs(
        organization_id=current_user.organization_id
    )


@router.post("/style-packs", response_model=StylePackResponse)
async def create_style_pack(
    payload: StylePackCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> StylePackResponse:
    return await DraftingService(session).create_style_pack(
        organization_id=current_user.organization_id,
        actor_user_id=current_user.id,
        request=payload,
    )


@router.get("/matters/{matter_id}/documents", response_model=list[DraftDocumentResponse])
async def list_drafts(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[DraftDocumentResponse]:
    return await DraftingService(session).list_drafts(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
    )


@router.post("/matters/{matter_id}/documents/generate", response_model=DraftDocumentResponse)
async def generate_draft(
    matter_id: UUID,
    payload: DraftGenerateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> DraftDocumentResponse:
    return await DraftingService(session).generate_draft(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        actor_user_id=current_user.id,
        request=payload,
    )


@router.get("/documents/{draft_id}", response_model=DraftDocumentResponse)
async def get_draft(
    draft_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> DraftDocumentResponse:
    return await DraftingService(session).get_draft(
        draft_id=draft_id,
        organization_id=current_user.organization_id,
    )


@router.get("/documents/{draft_id}/export", response_model=DraftExportResponse)
async def export_draft(
    draft_id: UUID,
    response_format: str = Query(default="json"),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    exported = await DraftingService(session).export_draft(
        draft_id=draft_id,
        organization_id=current_user.organization_id,
    )
    if response_format == "markdown":
        return PlainTextResponse(exported.content, media_type="text/markdown")
    return exported


@router.get("/documents/{draft_id}/redline", response_model=DraftRedlineResponse)
async def get_redline(
    draft_id: UUID,
    previous_version_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> DraftRedlineResponse:
    return await DraftingService(session).redline(
        draft_id=draft_id,
        organization_id=current_user.organization_id,
        previous_version_id=previous_version_id,
    )
