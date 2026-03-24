from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.research import SavedAuthority
from app.repositories.audit import AuditRepository
from app.repositories.drafting import DraftingRepository
from app.repositories.matters import MatterRepository
from app.schemas.strategy import (
    SequencingConsoleRequest,
    SequencingConsoleResponse,
    SequencingRecommendationResponse,
    StrategyIssueResponse,
    StrategyLineResponse,
    StrategyScenarioBranchResponse,
    StrategyWorkspaceResponse,
)
from app.services.bundle_analysis import BundleAnalysisService

PROMPT_ROOT = Path(__file__).resolve().parents[4] / "packages" / "prompts"


class StrategyService:
    def __init__(self, session) -> None:
        self.session = session
        self.matters = MatterRepository(session)
        self.drafting = DraftingRepository(session)
        self.audit = AuditRepository(session)

    async def get_workspace(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
    ) -> StrategyWorkspaceResponse:
        matter = await self.matters.get_by_id(matter_id, organization_id)
        if matter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

        saved_authorities = await self.drafting.list_saved_authorities_for_matter(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        try:
            bundle = await BundleAnalysisService(self.session).get_matter_bundle(
                matter_id=matter_id,
                organization_id=organization_id,
            )
        except ValueError:
            bundle = None

        issue_labels = self._issue_labels(bundle=bundle, saved_authorities=saved_authorities)
        if not issue_labels:
            issue_labels = ["Record completeness", "Interim relief posture"]

        issues = [
            self._issue_response(
                issue_label=issue,
                authorities=saved_authorities,
                bundle=bundle,
            )
            for issue in issue_labels[:4]
        ]

        contradiction_count = len(bundle.contradictions) if bundle is not None else 0
        best_line = StrategyLineResponse(
            label="Best line",
            summary=f"Lead with the cleanest documentary inconsistency on {issues[0].issue_label}.",
            rationale=(
                "The most persuasive line is the one with the shortest inferential jump from "
                "record gap to relief."
            ),
        )
        fallback_line = StrategyLineResponse(
            label="Fallback line",
            summary=(
                "If the court narrows relief, ask for record production and "
                "protective directions."
            ),
            rationale="This preserves procedural leverage even if merits relief is deferred.",
        )
        risk_line = StrategyLineResponse(
            label="Risk line",
            summary=(
                "Do not overstate facts that remain documentary gaps."
                if contradiction_count
                else "Do not convert suspicion into asserted fact without a source anchor."
            ),
            rationale=(
                "The system remains decision support only; unsupported certainty "
                "is the main advocacy risk."
            ),
        )

        scenario_tree = [
            StrategyScenarioBranchResponse(
                id=item["id"],
                label=item["label"],
                path=item["prompt"],
                next_step=self._branch_next_step(item["id"], issues[0].issue_label),
            )
            for item in self._load_branches()
        ]

        return StrategyWorkspaceResponse(
            matter_id=matter_id,
            objective=f"Advance {matter.title} with bounded issue-level decision support.",
            decision_support_label=(
                "Decision support only. Strategy outputs are bounded, reproducible "
                "summaries of the current record, not outcome prediction."
            ),
            best_line=best_line,
            fallback_line=fallback_line,
            risk_line=risk_line,
            issues=issues,
            scenario_tree=scenario_tree,
        )

    async def analyze_sequencing(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID,
        request: SequencingConsoleRequest,
    ) -> SequencingConsoleResponse:
        matter = await self.matters.get_by_id(matter_id, organization_id)
        if matter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

        recommendations = [self._classify_item(item.label, item.detail) for item in request.items]
        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="strategy.sequencing_reviewed",
            entity_type="matter",
            entity_id=str(matter_id),
            detail=f"{len(recommendations)} items",
        )
        await self.session.commit()
        return SequencingConsoleResponse(
            decision_support_label=(
                "Lawful sequencing console only. This tool may recommend "
                "disclosure, explanation, or reservation timing, but it must "
                "not be used to coach unlawful concealment."
            ),
            global_warning=(
                "Any statutory, court-directed, or mandatory fact should be "
                "treated as disclose-now or high-risk omission if the user "
                "proposes withholding it."
            ),
            items=recommendations,
        )

    @staticmethod
    def _issue_labels(*, bundle, saved_authorities: Sequence[SavedAuthority]) -> list[str]:
        labels: list[str] = []
        if bundle is not None:
            labels.extend(item.issue for item in bundle.contradictions)
            labels.extend(item.label for item in bundle.clusters if item.cluster_type == "issue")
        labels.extend(item.issue_label for item in saved_authorities)
        deduped: list[str] = []
        for label in labels:
            if label and label not in deduped:
                deduped.append(label)
        return deduped

    def _issue_response(
        self,
        *,
        issue_label: str,
        authorities: Sequence[SavedAuthority],
        bundle,
    ) -> StrategyIssueResponse:
        related_authorities = [
            item for item in authorities if issue_label.lower() in item.issue_label.lower()
        ] or authorities[:2]
        anchors = [item.quote_span.anchor_label for item in related_authorities if item.quote_span]
        contradiction_note = ""
        if bundle is not None:
            for contradiction in bundle.contradictions:
                if contradiction.issue == issue_label:
                    contradiction_note = contradiction.summary
                    break
        attack = (
            f"Press {issue_label} through the record anchor first, then show "
            "why the opposite version does not survive documentary scrutiny."
        )
        if contradiction_note:
            attack += f" Present the contradiction: {contradiction_note}"
        defense = (
            f"If the bench turns against you on {issue_label}, concede only "
            "what is documented and redirect to missing record production or "
            "narrower interim relief."
        )
        return StrategyIssueResponse(
            issue_label=issue_label,
            attack=attack,
            defense=defense,
            oral_short=f"{issue_label}: the record says less than the opposite side claims.",
            oral_detailed=(
                f"On {issue_label}, begin with the verified source span, "
                "identify the exact record gap or inconsistency, and then link "
                "that gap to the relief sought."
            ),
            written_note=(
                f"Written note for {issue_label}: proposition, source anchor, "
                "contradiction, and bounded relief ask."
            ),
            bench_questions=[
                f"What is the best source anchor for {issue_label}?",
                f"How does {issue_label} affect the relief sought at this stage?",
                f"What record should be called for if the court wants "
                f"confirmation on {issue_label}?",
            ],
            likely_opponent_attacks=[
                f"The record on {issue_label} is incomplete, not contradictory.",
                "Formal compliance should be presumed unless rebutted by a "
                "stronger source.",
            ],
            rebuttal_cards=[
                "Missing contemporaneous record is itself advocacy-significant.",
                "A formal assertion cannot outrun the document it claims to summarize.",
            ],
            authority_anchors=anchors,
        )

    @staticmethod
    def _branch_next_step(branch_id: str, issue_label: str) -> str:
        if branch_id == "record_gap":
            return f"Ask for the specific record that would resolve {issue_label}."
        if branch_id == "compliance_defense":
            return "Separate asserted compliance from documentary proof."
        return "Distinguish on stage, facts, and the safeguards actually shown in the record."

    @staticmethod
    def _load_branches() -> list[dict[str, str]]:
        payload = json.loads(
            (PROMPT_ROOT / "strategy" / "scenario_templates.json").read_text("utf-8")
        )
        return list(payload["branches"])

    @staticmethod
    def _classify_item(label: str, detail: str) -> SequencingRecommendationResponse:
        text = f"{label} {detail}".lower()
        if StrategyService._contains_phrase(
            text,
            ("hide", "suppress", "destroy", "withhold mandatory", "conceal"),
        ):
            return SequencingRecommendationResponse(
                label=label,
                bucket="high_risk_omission",
                recommendation="Do not omit this item without explicit legal basis and review.",
                reason="The phrasing suggests concealment rather than lawful sequencing.",
                mandatory_warning=True,
            )
        if StrategyService._contains_phrase(
            text,
            (
                "arrest",
                "custody",
                "medical",
                "injury",
                "limitation",
                "jurisdiction",
                "notice served",
                "age",
            ),
        ):
            return SequencingRecommendationResponse(
                label=label,
                bucket="disclose_now",
                recommendation="Disclose now with source anchor and context.",
                reason="This reads like a potentially mandatory or stage-critical fact.",
                mandatory_warning=True,
            )
        if StrategyService._contains_phrase(
            text,
            ("record gap", "delay", "omission", "contradiction"),
        ):
            return SequencingRecommendationResponse(
                label=label,
                bucket="explain_now",
                recommendation="Explain now with a confined correction and supporting source.",
                reason=(
                    "A known weakness generally needs framing before the other "
                    "side weaponizes it."
                ),
                mandatory_warning=False,
            )
        if StrategyService._contains_phrase(
            text,
            ("cross", "rebuttal", "impeach", "opponent inconsistency"),
        ):
            return SequencingRecommendationResponse(
                label=label,
                bucket="reserve_for_reply",
                recommendation=(
                    "Reserve for reply, rejoinder, or cross, but keep an "
                    "internal source map ready."
                ),
                reason=(
                    "This looks like an adversarial sequencing point rather "
                    "than a mandatory opening disclosure."
                ),
                mandatory_warning=False,
            )
        if StrategyService._contains_phrase(
            text,
            ("internal note", "settlement posture", "bench rehearsal", "work product"),
        ):
            return SequencingRecommendationResponse(
                label=label,
                bucket="internal_only",
                recommendation="Keep internal only unless converted into a filed position.",
                reason="This is internal strategy or work-product material.",
                mandatory_warning=False,
            )
        return SequencingRecommendationResponse(
            label=label,
            bucket="explain_now",
            recommendation="Explain now with a bounded note and a source anchor.",
            reason="Default to timely explanation when the disclosure posture is uncertain.",
            mandatory_warning=False,
        )

    @staticmethod
    def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
        return any(
            re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None
            for phrase in phrases
        )
