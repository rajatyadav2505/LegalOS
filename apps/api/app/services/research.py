from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.document import QuoteSpan
from app.domain.enums import DocumentSourceType
from app.domain.research import SavedAuthority
from app.repositories.audit import AuditRepository
from app.repositories.matters import MatterRepository
from app.repositories.research import ResearchRepository
from app.schemas.research import (
    ExportMemoResponse,
    ResearchSearchResponse,
    ResearchSearchResult,
    SaveAuthorityRequest,
    SavedAuthorityResponse,
)
from app.services.quote_lock import QuoteLockService


class ResearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ResearchRepository(session)
        self.matters = MatterRepository(session)
        self.audit = AuditRepository(session)

    async def search(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        query: str,
        authority_kind: str | None,
        court: str | None,
        issue: str | None,
        limit: int,
    ) -> ResearchSearchResponse:
        saved = await self.repository.get_saved_for_matter(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        saved_map = {item.quote_span_id: item.treatment for item in saved}
        results = await self.repository.search(
            organization_id=organization_id,
            matter_id=matter_id,
            query=query,
            authority_kind=authority_kind,
            court=court,
            issue=issue,
            limit=limit,
        )

        items = [
            ResearchSearchResult(
                document_id=row.document.id,
                quote_span_id=row.quote_span.id,
                title=row.document.title,
                citation_text=(
                    row.citation.citation_text
                    if row.citation
                    else row.document.citation_text
                ),
                authority_kind=row.document.authority_kind,
                source_type=row.document.source_type,
                court=row.citation.court if row.citation else row.document.court,
                forum=row.citation.forum if row.citation else row.document.forum,
                bench=row.citation.bench if row.citation else row.document.bench,
                decision_date=(
                    row.citation.decision_date if row.citation else row.document.decision_date
                ),
                legal_issue=row.citation.legal_issue if row.citation else row.document.legal_issue,
                anchor_label=row.quote_span.anchor_label,
                paragraph_start=row.quote_span.paragraph_start,
                paragraph_end=row.quote_span.paragraph_end,
                page_start=row.quote_span.page_start,
                page_end=row.quote_span.page_end,
                quote_text=row.quote_span.text,
                quote_checksum=row.quote_span.checksum,
                score=row.score,
                saved_treatment=saved_map.get(row.quote_span.id),
            )
            for row in results
        ]
        return ResearchSearchResponse(items=items, total=len(items))

    async def save_authority(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID,
        request: SaveAuthorityRequest,
    ) -> SavedAuthorityResponse:
        matter = await self.matters.get_by_id(matter_id, organization_id)
        if matter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matter not found",
            )

        quote_span = await self.repository.get_quote_span_for_organization(
            quote_span_id=request.quote_span_id,
            organization_id=organization_id,
        )
        if quote_span is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote span not found",
            )
        if (
            quote_span.document.source_type != DocumentSourceType.PUBLIC_LAW
            and quote_span.document.matter_id != matter_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote span is not available for this matter",
            )

        saved = SavedAuthority(
            matter_id=matter_id,
            citation_id=request.citation_id,
            quote_span_id=request.quote_span_id,
            created_by_user_id=actor_user_id,
            treatment=request.treatment,
            issue_label=request.issue_label,
            note=request.note,
        )
        self.session.add(saved)
        await self.session.flush()

        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="research.authority_saved",
            entity_type="saved_authority",
            entity_id=str(saved.id),
            detail=f"{request.treatment.value}:{request.issue_label}",
        )
        await self.session.commit()
        return SavedAuthorityResponse.model_validate(saved, from_attributes=True)

    async def export_memo(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> ExportMemoResponse:
        matter = await self.matters.get_by_id(matter_id, organization_id)
        if matter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matter not found",
            )

        saved = await self.repository.get_saved_for_matter(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        if not saved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No saved authorities found for this matter",
            )

        span_ids = [item.quote_span_id for item in saved]
        quote_spans = await self.repository.get_quote_spans_for_organization(
            quote_span_ids=span_ids,
            organization_id=organization_id,
        )
        span_map = {item.id: item for item in quote_spans}

        lines = ["# Research Memo", "", f"Matter: `{matter_id}`", ""]
        for item in saved:
            span = span_map[item.quote_span_id]
            lines.extend(
                [
                    f"## {item.issue_label}",
                    f"- Treatment: {item.treatment.value}",
                    f"- Anchor: {span.anchor_label}",
                    f"- Quote checksum: `{span.checksum}`",
                    f"- Quote: {span.text}",
                ]
            )
            if item.note:
                lines.append(f"- Note: {item.note}")
            lines.append("")

        return ExportMemoResponse(
            file_name=f"research-memo-{matter_id}.md",
            content="\n".join(lines).strip() + "\n",
        )

    async def quote_lock(
        self,
        *,
        quote_span_id: UUID,
        organization_id: UUID,
    ) -> tuple[QuoteSpan, str]:
        quote_span = await self.repository.get_quote_span_for_organization(
            quote_span_id=quote_span_id,
            organization_id=organization_id,
        )
        if quote_span is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote span not found",
            )
        if not QuoteLockService.matches(quote_span.text, quote_span.checksum):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stored quote span failed checksum validation",
            )
        return quote_span, quote_span.checksum
