from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.document import Document
from app.domain.matter import Matter
from app.domain.research import SavedAuthority


@dataclass(slots=True)
class MatterListRow:
    matter: Matter
    document_count: int
    saved_authority_count: int


class MatterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_organization(
        self,
        organization_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MatterListRow]:
        document_counts = (
            select(Document.matter_id, func.count(Document.id).label("document_count"))
            .group_by(Document.matter_id)
            .subquery()
        )
        saved_authority_counts = (
            select(
                SavedAuthority.matter_id,
                func.count(SavedAuthority.id).label("saved_authority_count"),
            )
            .group_by(SavedAuthority.matter_id)
            .subquery()
        )
        result = await self.session.execute(
            select(
                Matter,
                func.coalesce(document_counts.c.document_count, 0),
                func.coalesce(saved_authority_counts.c.saved_authority_count, 0),
            )
            .where(Matter.organization_id == organization_id)
            .outerjoin(document_counts, document_counts.c.matter_id == Matter.id)
            .outerjoin(saved_authority_counts, saved_authority_counts.c.matter_id == Matter.id)
            .order_by(Matter.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [
            MatterListRow(
                matter=row[0],
                document_count=int(row[1]),
                saved_authority_count=int(row[2]),
            )
            for row in result.all()
        ]

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
