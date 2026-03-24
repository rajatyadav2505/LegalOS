from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.repositories.matters import MatterRepository
from app.schemas.bundle import BundleMapResponse
from app.services.bundle_analysis import BundleAnalysisService

router = APIRouter()


@router.get("/{matter_id}/bundle", response_model=BundleMapResponse)
async def get_bundle_map(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> BundleMapResponse:
    matter = await MatterRepository(session).get_by_id(matter_id, current_user.organization_id)
    if matter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

    try:
        return await BundleAnalysisService(session).get_matter_bundle(
            matter_id=matter_id,
            organization_id=current_user.organization_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
