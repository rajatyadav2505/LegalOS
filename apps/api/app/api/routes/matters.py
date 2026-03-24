from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.repositories.matters import MatterRepository
from app.schemas.matter import MatterDetailResponse, MatterSummaryResponse

router = APIRouter()


@router.get("", response_model=list[MatterSummaryResponse])
async def list_matters(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> list[MatterSummaryResponse]:
    matters = await MatterRepository(session).list_for_organization(
        current_user.organization_id,
        limit=limit,
        offset=offset,
    )
    return [
        MatterSummaryResponse(
            id=item.matter.id,
            title=item.matter.title,
            reference_code=item.matter.reference_code,
            forum=item.matter.forum,
            stage=item.matter.stage,
            status=item.matter.status,
            next_hearing_date=item.matter.next_hearing_date,
            summary=item.matter.summary,
            updated_at=item.matter.updated_at,
            document_count=item.document_count,
            saved_authority_count=item.saved_authority_count,
        )
        for item in matters
    ]


@router.get("/{matter_id}", response_model=MatterDetailResponse)
async def get_matter(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> MatterDetailResponse:
    matter = await MatterRepository(session).get_by_id(matter_id, current_user.organization_id)
    if matter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")
    return MatterDetailResponse(
        id=matter.id,
        organization_id=matter.organization_id,
        owner_user_id=matter.owner_user_id,
        title=matter.title,
        reference_code=matter.reference_code,
        forum=matter.forum,
        stage=matter.stage,
        status=matter.status,
        next_hearing_date=matter.next_hearing_date,
        summary=matter.summary,
        updated_at=matter.updated_at,
        document_count=len(matter.documents),
        saved_authority_count=len(matter.saved_authorities),
    )
