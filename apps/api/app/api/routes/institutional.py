from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.schemas.institutional import (
    ApprovalCreateRequest,
    ApprovalResponse,
    ApprovalReviewRequest,
    InstitutionalDashboardResponse,
)
from app.services.institutional import InstitutionalService

router = APIRouter()


@router.get("/matters/{matter_id}/dashboard", response_model=InstitutionalDashboardResponse)
async def get_dashboard(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> InstitutionalDashboardResponse:
    return await InstitutionalService(session).get_dashboard(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
    )


@router.post("/matters/{matter_id}/approvals", response_model=ApprovalResponse)
async def request_approval(
    matter_id: UUID,
    payload: ApprovalCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ApprovalResponse:
    return await InstitutionalService(session).submit_approval(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        actor_user_id=current_user.id,
        request=payload,
    )


@router.post("/approvals/{approval_id}/review", response_model=ApprovalResponse)
async def review_approval(
    approval_id: UUID,
    payload: ApprovalReviewRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> ApprovalResponse:
    return await InstitutionalService(session).review_approval(
        organization_id=current_user.organization_id,
        approval_id=approval_id,
        actor_user_id=current_user.id,
        request=payload,
    )
