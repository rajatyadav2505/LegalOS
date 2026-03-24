from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.schemas.strategy import (
    SequencingConsoleRequest,
    SequencingConsoleResponse,
    StrategyWorkspaceResponse,
)
from app.services.strategy import StrategyService

router = APIRouter()


@router.get("/matters/{matter_id}/workspace", response_model=StrategyWorkspaceResponse)
async def get_strategy_workspace(
    matter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> StrategyWorkspaceResponse:
    return await StrategyService(session).get_workspace(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
    )


@router.post(
    "/matters/{matter_id}/sequencing-console",
    response_model=SequencingConsoleResponse,
)
async def review_sequencing(
    matter_id: UUID,
    payload: SequencingConsoleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
) -> SequencingConsoleResponse:
    return await StrategyService(session).analyze_sequencing(
        organization_id=current_user.organization_id,
        matter_id=matter_id,
        actor_user_id=current_user.id,
        request=payload,
    )
