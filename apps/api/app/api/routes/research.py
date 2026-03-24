from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.schemas.research import (
    ExportMemoResponse,
    QuoteLockResponse,
    ResearchSearchResponse,
    SaveAuthorityRequest,
    SavedAuthorityResponse,
)
from app.services.research import ResearchService

router = APIRouter()


@router.get("/search", response_model=ResearchSearchResponse)
async def search(
    matter_id: UUID,
    q: str = Query(..., min_length=2),
    authority_kind: str | None = Query(default=None),
    court: str | None = Query(default=None),
    issue: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=25),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ResearchSearchResponse:
    return await ResearchService(session).search(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        query=q,
        authority_kind=authority_kind,
        court=court,
        issue=issue,
        limit=limit,
    )


@router.post("/matters/{matter_id}/saved-authorities", response_model=SavedAuthorityResponse)
async def save_authority(
    matter_id: UUID,
    payload: SaveAuthorityRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> SavedAuthorityResponse:
    return await ResearchService(session).save_authority(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        actor_user_id=current_user.id,
        request=payload,
    )


@router.get("/quote-spans/{quote_span_id}", response_model=QuoteLockResponse)
async def get_quote_span(
    quote_span_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> QuoteLockResponse:
    quote_span, checksum = await ResearchService(session).quote_lock(
        quote_span_id=quote_span_id,
        organization_id=current_user.organization_id,
    )
    return QuoteLockResponse(
        quote_span_id=quote_span.id,
        anchor_label=quote_span.anchor_label,
        text=quote_span.text,
        checksum=checksum,
    )


@router.get("/matters/{matter_id}/export", response_model=ExportMemoResponse)
async def export_research_memo(
    matter_id: UUID,
    response_format: str = Query(default="json"),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    memo = await ResearchService(session).export_memo(
        matter_id=matter_id,
        organization_id=current_user.organization_id,
    )
    if response_format == "markdown":
        return PlainTextResponse(memo.content, media_type="text/markdown")
    return memo
