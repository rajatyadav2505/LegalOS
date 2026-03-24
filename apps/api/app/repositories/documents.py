from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, document_id: UUID, organization_id: UUID) -> Document | None:
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id, Document.organization_id == organization_id)
            .options(
                selectinload(Document.chunks),
                selectinload(Document.quote_spans),
                selectinload(Document.citations),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_matter(self, matter_id: UUID, organization_id: UUID) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.organization_id == organization_id, Document.matter_id == matter_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars())
