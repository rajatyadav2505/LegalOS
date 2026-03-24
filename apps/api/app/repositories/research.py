from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.document import Citation, Document, DocumentChunk, QuoteSpan
from app.domain.enums import DocumentSourceType
from app.domain.matter import Matter
from app.domain.research import SavedAuthority


@dataclass(slots=True)
class ResearchRow:
    document: Document
    chunk: DocumentChunk
    quote_span: QuoteSpan
    citation: Citation | None
    score: float


class ResearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _contains_pattern(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        return f"%{escaped}%"

    async def search(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        query: str,
        authority_kind: str | None = None,
        court: str | None = None,
        issue: str | None = None,
        limit: int = 12,
    ) -> list[ResearchRow]:
        base_stmt = (
            select(Document, DocumentChunk, QuoteSpan, Citation)
            .join(DocumentChunk, DocumentChunk.document_id == Document.id)
            .join(
                QuoteSpan,
                and_(
                    QuoteSpan.document_id == DocumentChunk.document_id,
                    QuoteSpan.paragraph_start == DocumentChunk.paragraph_start,
                    QuoteSpan.paragraph_end == DocumentChunk.paragraph_end,
                ),
            )
            .outerjoin(Citation, Citation.id == QuoteSpan.citation_id)
            .where(
                Document.organization_id == organization_id,
                or_(
                    Document.matter_id == matter_id,
                    Document.source_type == DocumentSourceType.PUBLIC_LAW,
                ),
            )
        )

        if authority_kind:
            base_stmt = base_stmt.where(Document.authority_kind == authority_kind)
        if court:
            base_stmt = base_stmt.where(
                Document.court.ilike(self._contains_pattern(court), escape="\\")
            )
        if issue:
            issue_pattern = self._contains_pattern(issue)
            base_stmt = base_stmt.where(
                or_(
                    Document.legal_issue.ilike(issue_pattern, escape="\\"),
                    Citation.legal_issue.ilike(issue_pattern, escape="\\"),
                )
            )

        dialect = self.session.bind.dialect.name if self.session.bind is not None else "unknown"
        if dialect == "postgresql":
            search_blob = func.concat_ws(
                " ",
                Document.title,
                DocumentChunk.text,
                func.coalesce(Document.legal_issue, ""),
                func.coalesce(Document.citation_text, ""),
                func.coalesce(Citation.citation_text, ""),
            )
            tsquery = func.websearch_to_tsquery("english", query)
            tsvector = func.to_tsvector("english", search_blob)
            result = await self.session.execute(
                base_stmt.add_columns(func.ts_rank_cd(tsvector, tsquery).label("score"))
                .where(tsvector.op("@@")(tsquery))
                .order_by(desc("score"))
                .limit(limit)
            )
            rows = result.all()
            return [
                ResearchRow(
                    document=row[0],
                    chunk=row[1],
                    quote_span=row[2],
                    citation=row[3],
                    score=float(row[4]),
                )
                for row in rows
            ]

        result = await self.session.execute(base_stmt)
        terms = [term.lower() for term in query.split() if term.strip()]
        ranked_rows: list[ResearchRow] = []
        for document, chunk, quote_span, citation in result.all():
            haystack = " ".join(
                filter(
                    None,
                    [
                        document.title,
                        document.legal_issue or "",
                        document.citation_text or "",
                        citation.citation_text if citation else "",
                        chunk.text,
                    ],
                )
            ).lower()
            score = float(sum(haystack.count(term) for term in terms))
            if score <= 0:
                continue
            ranked_rows.append(
                ResearchRow(
                    document=document,
                    chunk=chunk,
                    quote_span=quote_span,
                    citation=citation,
                    score=score,
                )
            )

        ranked_rows.sort(key=lambda item: item.score, reverse=True)
        return ranked_rows[:limit]

    async def get_saved_for_matter(
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
            .order_by(SavedAuthority.created_at.desc())
        )
        return list(result.scalars())

    async def get_quote_span_for_organization(
        self,
        *,
        quote_span_id: UUID,
        organization_id: UUID,
    ) -> QuoteSpan | None:
        result = await self.session.execute(
            select(QuoteSpan)
            .join(Document, Document.id == QuoteSpan.document_id)
            .where(
                QuoteSpan.id == quote_span_id,
                Document.organization_id == organization_id,
            )
            .options(selectinload(QuoteSpan.document))
        )
        return result.scalar_one_or_none()

    async def get_quote_spans_for_organization(
        self,
        *,
        quote_span_ids: list[UUID],
        organization_id: UUID,
    ) -> list[QuoteSpan]:
        if not quote_span_ids:
            return []
        result = await self.session.execute(
            select(QuoteSpan)
            .join(Document, Document.id == QuoteSpan.document_id)
            .where(
                QuoteSpan.id.in_(quote_span_ids),
                Document.organization_id == organization_id,
            )
        )
        return list(result.scalars())
