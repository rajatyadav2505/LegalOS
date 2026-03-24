from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.document import Document
from app.domain.matter import Matter
from app.domain.research import SavedAuthority


class MatterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_organization(self, organization_id: UUID) -> list[Matter]:
        result = await self.session.execute(
            select(Matter)
            .where(Matter.organization_id == organization_id)
            .options(
                selectinload(Matter.documents),
                selectinload(Matter.saved_authorities),
            )
            .order_by(Matter.updated_at.desc())
        )
        return list(result.scalars().unique())

    async def get_by_id(self, matter_id: UUID, organization_id: UUID) -> Matter | None:
        result = await self.session.execute(
            select(Matter)
            .where(Matter.id == matter_id, Matter.organization_id == organization_id)
            .options(
                selectinload(Matter.documents).selectinload(Document.quote_spans),
                selectinload(Matter.saved_authorities).selectinload(SavedAuthority.quote_span),
            )
        )
        return result.scalar_one_or_none()
