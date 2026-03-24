from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.bundle import ChronologyEvent, DocumentEntity, DocumentRelation, ExhibitReference
from app.domain.document import Document, QuoteSpan


@dataclass(slots=True)
class BundleSnapshot:
    documents: list[Document]
    quote_spans: list[QuoteSpan]
    chronology: list[ChronologyEvent]
    entities: list[DocumentEntity]
    exhibits: list[ExhibitReference]
    relations: list[DocumentRelation]


class BundleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def clear_document_artifacts(self, document_id: UUID) -> None:
        for model in (ChronologyEvent, DocumentEntity, ExhibitReference):
            await self.session.execute(delete(model).where(model.document_id == document_id))

    async def clear_matter_relations(self, matter_id: UUID) -> None:
        await self.session.execute(
            delete(DocumentRelation).where(DocumentRelation.matter_id == matter_id)
        )

    async def get_document(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
    ) -> Document | None:
        result = await self.session.execute(
            select(Document)
            .where(Document.id == document_id, Document.organization_id == organization_id)
            .options(selectinload(Document.quote_spans), selectinload(Document.matter))
        )
        return result.scalar_one_or_none()

    async def list_matter_documents(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(Document.organization_id == organization_id, Document.matter_id == matter_id)
            .options(selectinload(Document.quote_spans), selectinload(Document.matter))
            .order_by(Document.created_at.asc())
        )
        return list(result.scalars())

    async def load_snapshot(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> BundleSnapshot:
        documents = await self.list_matter_documents(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        document_ids = [item.id for item in documents]
        if not document_ids:
            return BundleSnapshot(
                documents=[],
                quote_spans=[],
                chronology=[],
                entities=[],
                exhibits=[],
                relations=[],
            )

        quote_spans = list(
            (
                await self.session.execute(
                    select(QuoteSpan).where(QuoteSpan.document_id.in_(document_ids))
                )
            ).scalars()
        )
        chronology = list(
            (
                await self.session.execute(
                    select(ChronologyEvent)
                    .where(ChronologyEvent.matter_id == matter_id)
                    .order_by(ChronologyEvent.event_date.asc(), ChronologyEvent.created_at.asc())
                )
            ).scalars()
        )
        entities = list(
            (
                await self.session.execute(
                    select(DocumentEntity).where(DocumentEntity.matter_id == matter_id)
                )
            ).scalars()
        )
        exhibits = list(
            (
                await self.session.execute(
                    select(ExhibitReference).where(ExhibitReference.matter_id == matter_id)
                )
            ).scalars()
        )
        relations = list(
            (
                await self.session.execute(
                    select(DocumentRelation).where(DocumentRelation.matter_id == matter_id)
                )
            ).scalars()
        )
        return BundleSnapshot(
            documents=documents,
            quote_spans=quote_spans,
            chronology=chronology,
            entities=entities,
            exhibits=exhibits,
            relations=relations,
        )
