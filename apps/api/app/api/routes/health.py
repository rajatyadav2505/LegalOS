from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import MessageResponse

router = APIRouter()


@router.get("/health", response_model=MessageResponse)
async def healthcheck() -> MessageResponse:
    return MessageResponse(message="ok")
