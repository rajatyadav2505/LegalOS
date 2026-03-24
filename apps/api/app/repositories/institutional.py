from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.audit import AuditEvent
from app.domain.drafting import DraftDocument
from app.domain.institutional import ApprovalRequest


class InstitutionalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_approvals_for_matter(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
    ) -> list[ApprovalRequest]:
        result = await self.session.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.organization_id == organization_id,
                ApprovalRequest.matter_id == matter_id,
            )
            .options(
                selectinload(ApprovalRequest.requested_by),
                selectinload(ApprovalRequest.reviewed_by),
            )
            .order_by(ApprovalRequest.created_at.desc())
        )
        return list(result.scalars())

    async def get_approval(
        self,
        *,
        approval_id: UUID,
        organization_id: UUID,
    ) -> ApprovalRequest | None:
        result = await self.session.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.id == approval_id,
                ApprovalRequest.organization_id == organization_id,
            )
            .options(
                selectinload(ApprovalRequest.requested_by),
                selectinload(ApprovalRequest.reviewed_by),
            )
        )
        return result.scalar_one_or_none()

    async def get_draft(
        self,
        *,
        draft_id: UUID,
        organization_id: UUID,
    ) -> DraftDocument | None:
        result = await self.session.execute(
            select(DraftDocument).where(
                DraftDocument.id == draft_id,
                DraftDocument.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_recent_audit_events(
        self,
        *,
        organization_id: UUID,
        limit: int = 25,
    ) -> list[AuditEvent]:
        result = await self.session.execute(
            select(AuditEvent)
            .where(AuditEvent.organization_id == organization_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())
