from __future__ import annotations

import json
import re
from collections.abc import Sequence
from difflib import unified_diff
from pathlib import Path
from typing import TypedDict, cast
from uuid import UUID

from fastapi import HTTPException, status

from app.domain.document import Document
from app.domain.drafting import (
    DraftAnnexure,
    DraftAuthorityLink,
    DraftDocument,
    DraftSection,
    StylePack,
)
from app.domain.enums import DocumentSourceType, DraftDocumentType, DraftStatus
from app.domain.research import SavedAuthority
from app.repositories.audit import AuditRepository
from app.repositories.drafting import DraftingRepository
from app.repositories.matters import MatterRepository
from app.schemas.drafting import (
    DraftAnnexureResponse,
    DraftAuthorityUseResponse,
    DraftDocumentResponse,
    DraftExportResponse,
    DraftGenerateRequest,
    DraftRedlineResponse,
    DraftRedlineSectionResponse,
    DraftSectionResponse,
    StylePackCreateRequest,
    StylePackResponse,
)
from app.services.bundle_analysis import BundleAnalysisService

PLACEHOLDER_PATTERN = re.compile(r"\[\[TODO:\s*(.*?)\]\]")
PROMPT_ROOT = Path(__file__).resolve().parents[4] / "packages" / "prompts"


class DraftSectionTemplate(TypedDict):
    key: str
    label: str
    required: bool


class DraftTemplate(TypedDict):
    label: str
    sections: list[DraftSectionTemplate]


class DraftingService:
    def __init__(self, session) -> None:
        self.session = session
        self.repository = DraftingRepository(session)
        self.matters = MatterRepository(session)
        self.audit = AuditRepository(session)

    async def list_style_packs(self, *, organization_id: UUID) -> list[StylePackResponse]:
        packs = await self.repository.list_style_packs(organization_id)
        return [self._style_pack_response(item) for item in packs]

    async def create_style_pack(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        request: StylePackCreateRequest,
    ) -> StylePackResponse:
        documents = await self.repository.list_documents_by_ids(
            organization_id=organization_id,
            document_ids=request.source_document_ids,
        )
        sample_titles = ", ".join(document.title for document in documents) or None
        voice_notes = request.voice_notes
        if documents and not voice_notes:
            voice_notes = self._derive_voice_notes(documents)

        style_pack = StylePack(
            organization_id=organization_id,
            created_by_user_id=actor_user_id,
            name=request.name,
            description=request.description,
            tone=request.tone,
            opening_phrase=request.opening_phrase,
            prayer_style=request.prayer_style,
            citation_style=request.citation_style,
            voice_notes=voice_notes,
            sample_document_titles=sample_titles,
        )
        self.session.add(style_pack)
        await self.session.flush()
        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="drafting.style_pack_created",
            entity_type="style_pack",
            entity_id=str(style_pack.id),
            detail=style_pack.name,
        )
        await self.session.commit()
        await self.session.refresh(style_pack)
        return self._style_pack_response(style_pack)

    async def list_drafts(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
    ) -> list[DraftDocumentResponse]:
        drafts = await self.repository.list_drafts_for_matter(
            organization_id=organization_id,
            matter_id=matter_id,
        )
        return [self._draft_response(item) for item in drafts]

    async def generate_draft(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID,
        actor_user_id: UUID,
        request: DraftGenerateRequest,
    ) -> DraftDocumentResponse:
        matter = await self.matters.get_by_id(matter_id, organization_id)
        if matter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Matter not found")

        style_pack = None
        if request.style_pack_id is not None:
            style_pack = await self.repository.get_style_pack(
                style_pack_id=request.style_pack_id,
                organization_id=organization_id,
            )
            if style_pack is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Style pack not found",
                )

        documents = await self.repository.list_documents_for_matter(
            organization_id=organization_id,
            matter_id=matter_id,
        )
        saved_authorities = await self.repository.list_saved_authorities_for_matter(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        if not request.include_saved_authorities:
            saved_authorities = []

        bundle = None
        if request.include_bundle_intelligence and documents:
            try:
                bundle = await BundleAnalysisService(self.session).get_matter_bundle(
                    matter_id=matter_id,
                    organization_id=organization_id,
                )
            except ValueError:
                bundle = None

        previous = await self.repository.get_previous_draft(
            matter_id=matter_id,
            document_type=request.document_type,
        )
        version_number = (previous.version_number + 1) if previous else 1

        template = self._load_templates().get(request.document_type.value)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No template configured for {request.document_type.value}",
            )
        placeholders = self._collect_placeholders(
            matter_summary=matter.summary or "",
            documents=documents,
            saved_authorities=saved_authorities,
            bundle=bundle,
        )
        annexure_documents = self._annexure_documents(
            documents=documents,
            selected_ids=request.annexure_document_ids,
        )

        draft = DraftDocument(
            organization_id=organization_id,
            matter_id=matter_id,
            created_by_user_id=actor_user_id,
            style_pack_id=style_pack.id if style_pack else None,
            previous_version_id=previous.id if previous else None,
            document_type=request.document_type,
            status=DraftStatus.DRAFT,
            title=request.title or f"{template['label']} for {matter.title}",
            version_number=version_number,
            summary=(
                f"Structured {request.document_type.value.replace('_', ' ')} built from matter "
                f"data, verified authorities, and bundle intelligence."
            ),
        )
        self.session.add(draft)
        await self.session.flush()

        section_bodies = self._compose_sections(
            document_type=request.document_type,
            matter_title=matter.title,
            forum=matter.forum,
            reference_code=matter.reference_code,
            matter_summary=matter.summary or "",
            style_pack=style_pack,
            bundle=bundle,
            saved_authorities=saved_authorities,
            annexure_documents=annexure_documents,
            placeholders=placeholders,
        )

        for index, section_template in enumerate(template["sections"], start=1):
            body_text = section_bodies.get(section_template["key"], "")
            self.session.add(
                DraftSection(
                    draft_document_id=draft.id,
                    section_key=section_template["key"],
                    label=section_template["label"],
                    body_text=body_text,
                    order_index=index,
                    is_required=bool(section_template.get("required", True)),
                    placeholder_count=len(PLACEHOLDER_PATTERN.findall(body_text)),
                )
            )

        for position, saved_authority in enumerate(saved_authorities, start=1):
            self.session.add(
                DraftAuthorityLink(
                    draft_document_id=draft.id,
                    saved_authority_id=saved_authority.id,
                    section_key=self._authority_section_key(request.document_type),
                    position_index=position,
                )
            )

        for index, document in enumerate(annexure_documents, start=1):
            self.session.add(
                DraftAnnexure(
                    draft_document_id=draft.id,
                    source_document_id=document.id,
                    label=f"Annexure P-{index}",
                    title=document.title,
                    note=document.legal_issue,
                    order_index=index,
                )
            )

        await self.audit.record(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action="drafting.document_generated",
            entity_type="draft_document",
            entity_id=str(draft.id),
            detail=f"{draft.document_type.value}:v{draft.version_number}",
        )
        await self.session.commit()
        loaded = await self.repository.get_draft(draft_id=draft.id, organization_id=organization_id)
        if loaded is None:
            raise HTTPException(status_code=500, detail="Draft generation failed")
        return self._draft_response(loaded)

    async def get_draft(
        self,
        *,
        draft_id: UUID,
        organization_id: UUID,
    ) -> DraftDocumentResponse:
        draft = await self.repository.get_draft(draft_id=draft_id, organization_id=organization_id)
        if draft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
        return self._draft_response(draft)

    async def export_draft(
        self,
        *,
        draft_id: UUID,
        organization_id: UUID,
    ) -> DraftExportResponse:
        draft = await self.repository.get_draft(draft_id=draft_id, organization_id=organization_id)
        if draft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

        lines = [
            f"# {draft.title}",
            "",
            f"- Document type: {draft.document_type.value}",
            f"- Version: {draft.version_number}",
        ]
        if draft.style_pack:
            lines.append(f"- Style pack: {draft.style_pack.name}")
        lines.append("")
        for section in draft.sections:
            lines.extend([f"## {section.label}", section.body_text, ""])
        if draft.annexures:
            lines.append("## Annexure Index")
            for annexure in draft.annexures:
                lines.append(f"- {annexure.label}: {annexure.title}")
            lines.append("")

        file_name = f"{draft.document_type.value}-{draft.matter_id}-v{draft.version_number}.md"
        draft.export_file_name = file_name
        draft.status = DraftStatus.EXPORTED
        await self.session.commit()
        return DraftExportResponse(file_name=file_name, content="\n".join(lines).strip() + "\n")

    async def redline(
        self,
        *,
        draft_id: UUID,
        organization_id: UUID,
        previous_version_id: UUID | None = None,
    ) -> DraftRedlineResponse:
        draft = await self.repository.get_draft(draft_id=draft_id, organization_id=organization_id)
        if draft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

        previous = None
        if previous_version_id:
            previous = await self.repository.get_draft(
                draft_id=previous_version_id,
                organization_id=organization_id,
            )
        elif draft.previous_version_id:
            previous = await self.repository.get_draft(
                draft_id=draft.previous_version_id,
                organization_id=organization_id,
            )
        if previous is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Previous draft version not found",
            )

        previous_sections = {item.section_key: item for item in previous.sections}
        diffs: list[DraftRedlineSectionResponse] = []
        for section in draft.sections:
            old_body = previous_sections.get(section.section_key)
            diff = "\n".join(
                unified_diff(
                    (old_body.body_text if old_body else "").splitlines(),
                    section.body_text.splitlines(),
                    fromfile=f"{section.section_key}@v{previous.version_number}",
                    tofile=f"{section.section_key}@v{draft.version_number}",
                    lineterm="",
                )
            )
            diffs.append(
                DraftRedlineSectionResponse(
                    section_key=section.section_key,
                    label=section.label,
                    diff=diff or "No textual changes detected.",
                )
            )
        return DraftRedlineResponse(
            current_draft_id=draft.id,
            previous_draft_id=previous.id,
            sections=diffs,
        )

    def _load_templates(self) -> dict[str, DraftTemplate]:
        payload = json.loads(
            (PROMPT_ROOT / "drafting" / "document_templates.json").read_text("utf-8")
        )
        return cast(dict[str, DraftTemplate], payload)

    @staticmethod
    def _derive_voice_notes(documents: list[Document]) -> str:
        lower_blob = " ".join(
            (document.extracted_text or "")[:1200] for document in documents
        ).lower()
        parts: list[str] = []
        if "most respectfully" in lower_blob:
            parts.append("Uses restrained court-facing formality.")
        if "it is submitted" in lower_blob:
            parts.append("Prefers direct proposition-led openings.")
        if "therefore prayed" in lower_blob or "prayed that" in lower_blob:
            parts.append("Uses concise prayer clauses.")
        return " ".join(parts) or (
            "Use short proposition-led paragraphs and restrained courtroom formality."
        )

    @staticmethod
    def _annexure_documents(
        *,
        documents: list[Document],
        selected_ids: list[UUID],
    ) -> list[Document]:
        matter_documents = [
            item for item in documents if item.source_type != DocumentSourceType.PUBLIC_LAW
        ]
        if selected_ids:
            selected = [item for item in matter_documents if item.id in set(selected_ids)]
            return selected[:8]
        return matter_documents[:8]

    @staticmethod
    def _collect_placeholders(
        *,
        matter_summary: str,
        documents: list[Document],
        saved_authorities: Sequence[SavedAuthority],
        bundle,
    ) -> list[str]:
        placeholders: list[str] = []
        if not matter_summary:
            placeholders.append("Confirm concise matter summary and case posture.")
        if not any(item.source_type == "opponent_document" for item in documents):
            placeholders.append("Upload or summarize the opponent's pleading before final filing.")
        if not any(item.source_type == "court_document" for item in documents):
            placeholders.append("Upload the latest court order or remand record.")
        if not saved_authorities:
            placeholders.append("Save at least one verified authority before settling the draft.")
        if bundle is None or not bundle.chronology:
            placeholders.append("Confirm the operative chronology from source records.")
        return placeholders

    def _compose_sections(
        self,
        *,
        document_type: DraftDocumentType,
        matter_title: str,
        forum: str,
        reference_code: str,
        matter_summary: str,
        style_pack: StylePack | None,
        bundle,
        saved_authorities: Sequence[SavedAuthority],
        annexure_documents: list[Document],
        placeholders: list[str],
    ) -> dict[str, str]:
        chronology_lines = []
        if bundle is not None:
            chronology_lines = [
                f"- {item.date}: {item.title} ({item.anchor_label})"
                for item in bundle.chronology[:5]
            ]
        contradiction_lines = []
        if bundle is not None:
            contradiction_lines = [
                f"- {item.issue}: {item.summary}"
                for item in bundle.contradictions[:3]
            ]
        authority_lines = []
        for saved in saved_authorities:
            quote_span = saved.quote_span
            citation_text = saved.citation.citation_text if saved.citation else None
            authority_lines.append(
                f"- {saved.issue_label} [{saved.treatment.value}] "
                f"{citation_text or 'Verified span'} | {quote_span.anchor_label} | "
                f"checksum `{quote_span.checksum}` | \"{quote_span.text}\""
            )

        opening = (
            style_pack.opening_phrase
            if style_pack is not None
            else "It is most respectfully submitted"
        )
        prayer_style = (
            style_pack.prayer_style
            if style_pack is not None
            else "It is therefore most respectfully prayed"
        )
        tone_line = (
            f"Style note: {style_pack.tone}. {style_pack.voice_notes or ''}".strip()
            if style_pack is not None
            else "Style note: use restrained, proposition-led courtroom prose."
        )
        placeholder_block = "\n".join(
            f"- [[TODO: {item}]]"
            for item in placeholders
        )
        annexure_lines = [
            f"- Annexure P-{index}: {document.title}"
            for index, document in enumerate(annexure_documents, start=1)
        ]

        base = {
            "case_overview": "\n".join(
                [
                    f"{opening} in {matter_title} before the {forum}.",
                    f"Reference code: {reference_code}.",
                    matter_summary or "[[TODO: Add a concise overview of the dispute.]]",
                    tone_line,
                ]
            ),
            "facts": "\n".join(
                [
                    "The presently verified chronology is:",
                    *(
                        chronology_lines
                        or ["- [[TODO: Confirm chronology from uploaded records.]]"]
                    ),
                    "",
                    "Open factual items requiring confirmation:",
                    placeholder_block or "- None presently flagged.",
                ]
            ),
            "issues": "\n".join(
                [
                    "The draft should be organized around the following issues:",
                    *(contradiction_lines or ["- Procedural fairness and record completeness."]),
                ]
            ),
            "grounds": "\n".join(
                [
                    "Grounds presently supported by the uploaded bundle and verified authorities:",
                    "- The record must match the asserted procedural compliance.",
                    "- Any contradiction on counsel, family notice, or custody "
                    "chronology should be confronted directly.",
                    "- Unsupported assertions should not be advanced without "
                    "documentary or affidavit support.",
                    placeholder_block or "",
                ]
            ),
            "authorities": "\n".join(
                [
                    "Only the following saved authorities may be inserted as verified support:",
                    *(
                        authority_lines
                        or [
                            "- [[TODO: Save verified authorities before "
                            "finalizing the draft.]]"
                        ]
                    ),
                ]
            ),
            "prayer": "\n".join(
                [
                    f"{prayer_style}:",
                    "- grant appropriate interim and final relief consistent "
                    "with the verified record;",
                    "- call for the relevant custody, arrest, or notice "
                    "records if gaps persist;",
                    "- pass any further order required in the interests of justice.",
                ]
            ),
            "annexures": "\n".join(
                [
                    "Proposed annexure schedule:",
                    *(annexure_lines or ["- [[TODO: Identify supporting annexures.]]"]),
                ]
            ),
            "response_frame": "\n".join(
                [
                    f"{opening}. This reply addresses the pleaded assertions issue by issue.",
                    "Admissions should remain narrow and every denial should "
                    "be tied to an identified source.",
                    tone_line,
                ]
            ),
            "pointwise_reply": "\n".join(
                [
                    "Pointwise reply frame:",
                    *(
                        contradiction_lines
                        or [
                            "- Answer each pleaded factual assertion against "
                            "the uploaded record."
                        ]
                    ),
                    placeholder_block or "",
                ]
            ),
            "distinguishing_authorities": "\n".join(
                [
                    "Distinguish adverse propositions only through saved "
                    "authorities and record-specific differences:",
                    *(
                        authority_lines
                        or [
                            "- [[TODO: Save adverse and distinguishing "
                            "authorities first.]]"
                        ]
                    ),
                ]
            ),
            "issue_matrix": "\n".join(
                [
                    "Issue matrix for hearing:",
                    *(
                        contradiction_lines
                        or [
                            "- Record completeness",
                            "- Counsel access",
                            "- Relief justification",
                        ]
                    ),
                ]
            ),
            "arguments": "\n".join(
                [
                    "Written arguments should proceed proposition first, then "
                    "record anchor, then authority support.",
                    "Each proposition must point back to one verified source "
                    "span or one uploaded document.",
                    placeholder_block or "",
                ]
            ),
            "relief_sought": "\n".join(
                [
                    "Application frame:",
                    "- Identify the narrow procedural or substantive relief sought.",
                    "- Explain urgency, prejudice, and record basis.",
                ]
            ),
            "factual_basis": "\n".join(
                [
                    "Factual basis:",
                    *(
                        chronology_lines
                        or [
                            "- [[TODO: Confirm the factual basis from source "
                            "records.]]"
                        ]
                    ),
                ]
            ),
            "legal_basis": "\n".join(
                [
                    "Legal basis:",
                    *(
                        authority_lines
                        or [
                            "- [[TODO: Insert verified legal basis from saved "
                            "authorities.]]"
                        ]
                    ),
                ]
            ),
            "deponent_details": "\n".join(
                [
                    "Deponent details:",
                    f"- Matter: {matter_title}",
                    f"- Forum: {forum}",
                    "- State the deponent's role, authority, and basis of knowledge.",
                ]
            ),
            "affirmed_facts": "\n".join(
                [
                    "Affirmed facts:",
                    *(
                        chronology_lines
                        or [
                            "- [[TODO: Set out the affidavit facts from the "
                            "record and personal knowledge.]]"
                        ]
                    ),
                    "",
                    placeholder_block or "- No open factual confirmations.",
                ]
            ),
            "verification_clause": "\n".join(
                [
                    "Verification:",
                    "- Confirm which paragraphs are based on personal knowledge.",
                    "- Identify which statements are based on records or legal advice.",
                    "- Add place, date, and attestation details before filing.",
                ]
            ),
            "date_entries": "\n".join(
                [
                    "List of dates:",
                    *(
                        chronology_lines
                        or [
                            "- [[TODO: Populate the dated chronology from the "
                            "bundle and court record.]]"
                        ]
                    ),
                ]
            ),
            "notice_background": "\n".join(
                [
                    f"{opening}. This legal notice concerns {matter_title}.",
                    matter_summary or "[[TODO: Add the material background facts.]]",
                    tone_line,
                ]
            ),
            "notice_demands": "\n".join(
                [
                    "Demands in notice:",
                    "- Call for compliance or corrective action within a stated timeline.",
                    "- Preserve a documentary trail for any non-compliance.",
                    placeholder_block or "",
                ]
            ),
            "settlement_background": "\n".join(
                [
                    "Settlement note background:",
                    matter_summary or "[[TODO: Add settlement posture and key facts.]]",
                    "This note is internal unless expressly converted into a shared proposal.",
                ]
            ),
            "settlement_terms": "\n".join(
                [
                    "Possible settlement terms:",
                    "- State the minimum acceptable record correction or relief.",
                    "- Identify non-negotiable safeguards, timelines, and compliance checkpoints.",
                    placeholder_block or "",
                ]
            ),
            "risk_reservation": "\n".join(
                [
                    "Risk and reservation note:",
                    "- Preserve litigation positions not intended for compromise.",
                    "- Record any authority or factual gap that prevents final settlement advice.",
                ]
            ),
        }
        return base

    @staticmethod
    def _authority_section_key(document_type: DraftDocumentType) -> str:
        mapping = {
            DraftDocumentType.REPLY: "distinguishing_authorities",
            DraftDocumentType.APPLICATION: "legal_basis",
            DraftDocumentType.AFFIDAVIT: "affirmed_facts",
            DraftDocumentType.LEGAL_NOTICE: "legal_basis",
            DraftDocumentType.SETTLEMENT_NOTE: "risk_reservation",
        }
        return mapping.get(document_type, "authorities")

    def _style_pack_response(self, style_pack: StylePack) -> StylePackResponse:
        return StylePackResponse(
            id=style_pack.id,
            name=style_pack.name,
            description=style_pack.description,
            tone=style_pack.tone,
            opening_phrase=style_pack.opening_phrase,
            prayer_style=style_pack.prayer_style,
            citation_style=style_pack.citation_style,
            voice_notes=style_pack.voice_notes,
            sample_document_titles=style_pack.sample_document_titles,
            created_at=style_pack.created_at,
        )

    def _draft_response(self, draft: DraftDocument) -> DraftDocumentResponse:
        unresolved_placeholders: list[str] = []
        sections = []
        for section in draft.sections:
            sections.append(
                DraftSectionResponse(
                    id=section.id,
                    section_key=section.section_key,
                    label=section.label,
                    body_text=section.body_text,
                    order_index=section.order_index,
                    is_required=section.is_required,
                    placeholder_count=section.placeholder_count,
                )
            )
            unresolved_placeholders.extend(PLACEHOLDER_PATTERN.findall(section.body_text))

        authorities_used = []
        for link in draft.authority_links:
            saved_authority = link.saved_authority
            quote_span = saved_authority.quote_span
            authorities_used.append(
                DraftAuthorityUseResponse(
                    id=link.id,
                    saved_authority_id=saved_authority.id,
                    issue_label=saved_authority.issue_label,
                    treatment=saved_authority.treatment.value,
                    section_key=link.section_key,
                    anchor_label=quote_span.anchor_label,
                    quote_text=quote_span.text,
                    checksum=quote_span.checksum,
                    citation_text=(
                        saved_authority.citation.citation_text
                        if saved_authority.citation
                        else None
                    ),
                )
            )

        annexures = [
            DraftAnnexureResponse(
                id=item.id,
                label=item.label,
                title=item.title,
                note=item.note,
                source_document_id=item.source_document_id,
            )
            for item in draft.annexures
        ]

        return DraftDocumentResponse(
            id=draft.id,
            matter_id=draft.matter_id,
            title=draft.title,
            document_type=draft.document_type,
            status=draft.status,
            version_number=draft.version_number,
            summary=draft.summary,
            export_file_name=draft.export_file_name,
            style_pack=self._style_pack_response(draft.style_pack) if draft.style_pack else None,
            sections=sections,
            authorities_used=authorities_used,
            annexures=annexures,
            unresolved_placeholders=unresolved_placeholders,
            created_at=draft.created_at,
        )
