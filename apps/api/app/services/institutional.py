from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.enums import ApprovalStatus, ApprovalTargetType
from app.domain.institutional import ApprovalRequest
from app.repositories.audit import AuditRepository
from app.repositories.drafting import DraftingRepository
from app.repositories.institutional import InstitutionalRepository
from app.repositories.matters import MatterRepository
from app.schemas.institutional import (
    ApprovalCreateRequest,
    ApprovalResponse,
    ApprovalReviewRequest,
    AuditEventResponse,
    InstitutionalDashboardResponse,
)
from app.services.strategy import StrategyService


class InstitutionalService:
    def __init__(self, session) -> None:
        self.session = session
        self.audit = AuditRepository(session)
        self.matters = MatterRepository(session)
        self.drafting = DraftingRepository(session)
        self.repository = InstitutionalRepository(session)

    async def submit_approval(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID,
        request: ApprovalCreateRequest,
    ) -> ApprovalResponse:
        matter = await self.matters.get_by_id(matter_id, organization_id)
        if matter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")
        if request.target_type == ApprovalTargetType.DRAFT_DOCUMENT:
            draft = await self.repository.get_draft(
                draft_id=request.target_id,
                organization_id=organization_id,
            )
            if draft is None or draft.matter_id != matter_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

        approval = ApprovalRequest(
            organization_id=organization_id,
            matter_id=matter_id,
            requested_by_user_id=actor_user_id,
            target_type=request.target_type,
            target_id=str(request.target_id),
            status=ApprovalStatus.PENDING,
            note=request.note,
        )
        self.session.add(approval)
        await self.session.flush()
        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="institutional.approval_requested",
            entity_type="approval_request",
            entity_id=str(approval.id),
            detail=f"{approval.target_type.value}:{approval.target_id}",
        )
        await self.session.commit()
        await self.session.refresh(approval)
        return self._approval_response(approval)

    async def review_approval(
        self,
        *,
        organization_id: UUID,
        approval_id: UUID,
        actor_user_id: UUID,
        request: ApprovalReviewRequest,
    ) -> ApprovalResponse:
        approval = await self.repository.get_approval(
            approval_id=approval_id,
            organization_id=organization_id,
        )
        if approval is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")

        approval.status = request.status
        approval.review_note = request.review_note
        approval.reviewed_by_user_id = actor_user_id
        approval.reviewed_at = datetime.now(UTC)
        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="institutional.approval_reviewed",
            entity_type="approval_request",
            entity_id=str(approval.id),
            detail=request.status.value,
        )
        await self.session.commit()
        await self.session.refresh(approval)
        return self._approval_response(approval)

    async def get_dashboard(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
    ) -> InstitutionalDashboardResponse:
        matter = await self.matters.get_by_id(matter_id, organization_id)
        if matter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

        approvals = await self.repository.list_approvals_for_matter(
            organization_id=organization_id,
            matter_id=matter_id,
        )
        drafts = await self.drafting.list_drafts_for_matter(
            organization_id=organization_id,
            matter_id=matter_id,
        )
        recent_audit_events = await self.audit.list_recent_for_organization(
            organization_id=organization_id,
            limit=12,
        )
        strategy = await StrategyService(self.session).get_workspace(
            organization_id=organization_id,
            matter_id=matter_id,
        )

        days_to_hearing = self._days_to_hearing(matter.next_hearing_date)
        urgency_status = self._urgency_status(days_to_hearing)
        pending_approvals = sum(1 for item in approvals if item.status == ApprovalStatus.PENDING)
        latest_draft_id = drafts[0].id if drafts else None

        plain_language_en = (
            "This matter is currently in the "
            f"{matter.stage.value.replace('_', ' ')} stage before the "
            f"{matter.forum}. "
            f"The best present line is: {strategy.best_line.summary} "
            "This summary is for coordination and client communication, "
            "not a guarantee of outcome."
        )
        plain_language_hi = (
            f"Yeh matter abhi {matter.forum} ke saamne "
            f"{matter.stage.value.replace('_', ' ')} stage par hai. "
            f"Is samay sabse mazboot line yeh hai: {strategy.best_line.summary} "
            "Yeh sirf samajh aur tayari ke liye hai, parinam ki guarantee nahin."
        )

        return InstitutionalDashboardResponse(
            matter_id=matter_id,
            urgency_status=urgency_status,
            days_to_hearing=days_to_hearing,
            pending_approvals=pending_approvals,
            latest_draft_id=latest_draft_id,
            approvals=[self._approval_response(item) for item in approvals],
            recent_audit_events=[
                AuditEventResponse(
                    id=item.id,
                    action=item.action,
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    detail=item.detail,
                    created_at=item.created_at,
                )
                for item in recent_audit_events
            ],
            plain_language_en=plain_language_en,
            plain_language_hi=plain_language_hi,
            low_bandwidth_brief=[
                f"Urgency: {urgency_status}",
                f"Pending approvals: {pending_approvals}",
                f"Best line: {strategy.best_line.summary}",
                f"Fallback line: {strategy.fallback_line.summary}",
            ],
            decision_support_label=(
                "Institutional mode increases auditability and approval "
                "visibility. Strategy and plain-language outputs remain "
                "decision support only."
            ),
        )

    @staticmethod
    def _days_to_hearing(next_hearing_date: date | None) -> int | None:
        if next_hearing_date is None:
            return None
        return (next_hearing_date - date.today()).days

    @staticmethod
    def _urgency_status(days_to_hearing: int | None) -> str:
        if days_to_hearing is None:
            return "unscheduled"
        if days_to_hearing <= 3:
            return "urgent"
        if days_to_hearing <= 14:
            return "upcoming"
        return "steady"

    @staticmethod
    def _approval_response(approval: ApprovalRequest) -> ApprovalResponse:
        return ApprovalResponse(
            id=approval.id,
            matter_id=approval.matter_id,
            target_type=approval.target_type,
            target_id=approval.target_id,
            status=approval.status,
            note=approval.note,
            review_note=approval.review_note,
            requested_by_user_id=approval.requested_by_user_id,
            reviewed_by_user_id=approval.reviewed_by_user_id,
            reviewed_at=approval.reviewed_at,
            created_at=approval.created_at,
        )
