from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.document import Document, QuoteSpan
from app.domain.drafting import (
    DraftAnnexure,
    DraftAuthorityLink,
    DraftDocument,
    StylePack,
)
from app.domain.enums import DraftDocumentType
from app.domain.matter import Matter
from app.domain.research import SavedAuthority


class DraftingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_style_packs(self, organization_id: UUID) -> list[StylePack]:
        result = await self.session.execute(
            select(StylePack)
            .where(StylePack.organization_id == organization_id)
            .order_by(StylePack.created_at.desc())
        )
        return list(result.scalars())

    async def get_style_pack(
        self,
        *,
        style_pack_id: UUID,
        organization_id: UUID,
    ) -> StylePack | None:
        result = await self.session.execute(
            select(StylePack).where(
                StylePack.id == style_pack_id,
                StylePack.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_documents_for_matter(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
    ) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.matter_id == matter_id,
            )
            .options(selectinload(Document.quote_spans))
            .order_by(Document.created_at.asc())
        )
        return list(result.scalars())

    async def list_documents_by_ids(
        self,
        *,
        organization_id: UUID,
        document_ids: list[UUID],
    ) -> list[Document]:
        if not document_ids:
            return []
        result = await self.session.execute(
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.id.in_(document_ids),
            )
            .options(selectinload(Document.quote_spans))
            .order_by(Document.created_at.asc())
        )
        return list(result.scalars())

    async def list_saved_authorities_for_matter(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> list[SavedAuthority]:
        result = await self.session.execute(
            select(SavedAuthority)
            .join(Matter, Matter.id == SavedAuthority.matter_id)
            .where(
                SavedAuthority.matter_id == matter_id,
                Matter.organization_id == organization_id,
            )
            .options(
                selectinload(SavedAuthority.quote_span),
                selectinload(SavedAuthority.citation),
            )
            .order_by(SavedAuthority.created_at.asc())
        )
        return list(result.scalars())

    async def get_latest_version_number(
        self,
        *,
        matter_id: UUID,
        document_type: DraftDocumentType,
    ) -> int:
        result = await self.session.execute(
            select(func.max(DraftDocument.version_number)).where(
                DraftDocument.matter_id == matter_id,
                DraftDocument.document_type == document_type,
            )
        )
        return int(result.scalar_one() or 0)

    async def get_previous_draft(
        self,
        *,
        matter_id: UUID,
        document_type: DraftDocumentType,
    ) -> DraftDocument | None:
        result = await self.session.execute(
            select(DraftDocument)
            .where(
                DraftDocument.matter_id == matter_id,
                DraftDocument.document_type == document_type,
            )
            .options(
                selectinload(DraftDocument.sections),
                selectinload(DraftDocument.annexures),
                selectinload(DraftDocument.authority_links),
            )
            .order_by(DraftDocument.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_drafts_for_matter(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
    ) -> list[DraftDocument]:
        result = await self.session.execute(
            select(DraftDocument)
            .where(
                DraftDocument.organization_id == organization_id,
                DraftDocument.matter_id == matter_id,
            )
            .options(
                selectinload(DraftDocument.style_pack),
                selectinload(DraftDocument.sections),
                selectinload(DraftDocument.annexures),
                selectinload(DraftDocument.authority_links),
            )
            .order_by(DraftDocument.created_at.desc())
        )
        return list(result.scalars())

    async def get_draft(
        self,
        *,
        draft_id: UUID,
        organization_id: UUID,
    ) -> DraftDocument | None:
        result = await self.session.execute(
            select(DraftDocument)
            .where(
                DraftDocument.id == draft_id,
                DraftDocument.organization_id == organization_id,
            )
            .options(
                selectinload(DraftDocument.style_pack),
                selectinload(DraftDocument.sections),
                selectinload(DraftDocument.annexures).selectinload(DraftAnnexure.source_document),
                selectinload(DraftDocument.authority_links)
                .selectinload(DraftAuthorityLink.saved_authority)
                .selectinload(SavedAuthority.quote_span),
                selectinload(DraftDocument.authority_links)
                .selectinload(DraftAuthorityLink.saved_authority)
                .selectinload(SavedAuthority.citation),
                selectinload(DraftDocument.previous_version).selectinload(DraftDocument.sections),
            )
        )
        return result.scalar_one_or_none()

    async def get_quote_spans(self, span_ids: list[UUID]) -> dict[UUID, QuoteSpan]:
        if not span_ids:
            return {}
        result = await self.session.execute(select(QuoteSpan).where(QuoteSpan.id.in_(span_ids)))
        return {item.id: item for item in result.scalars()}
