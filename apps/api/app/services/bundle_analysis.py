from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime
from difflib import SequenceMatcher
from itertools import combinations
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.bundle import ChronologyEvent, DocumentEntity, DocumentRelation, ExhibitReference
from app.domain.document import Document, QuoteSpan
from app.domain.enums import EntityType, ProcessingStatus, RelationSeverity, RelationType
from app.repositories.bundle import BundleRepository
from app.schemas.bundle import (
    BundleChronologyItemResponse,
    BundleClusterResponse,
    BundleContradictionResponse,
    BundleDocumentSummaryResponse,
    BundleDuplicateGroupResponse,
    BundleDuplicateMemberResponse,
    BundleExhibitLinkResponse,
    BundleMapResponse,
    BundleProcessingOverviewResponse,
    BundleProcessingStageResponse,
)

DATE_PATTERN = re.compile(r"\b(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\b")
PROPER_NOUN_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b")
WHITESPACE_PATTERN = re.compile(r"\s+")

ROLE_LABELS: dict[str, str] = {
    "petitioner": "Petitioner",
    "state": "State",
    "detenue": "Detenue",
    "duty magistrate": "Duty Magistrate",
    "magistrate": "Magistrate",
    "counsel": "Counsel",
    "lawyer": "Lawyer",
    "legal aid": "Legal Aid",
    "family": "Family",
    "relative": "Relative",
}

EXHIBIT_PATTERNS: dict[str, tuple[str, ...]] = {
    "Arrest Memo Extract": ("arrest memo extract", "arrest memo"),
    "Remand Sheet Extract": ("remand sheet",),
    "Production Papers": ("production papers", "first production papers"),
}

SEVERITY_ORDER = {
    RelationSeverity.HIGH: 0,
    RelationSeverity.MEDIUM: 1,
    RelationSeverity.LOW: 2,
}


@dataclass(slots=True)
class ClaimSignal:
    topic: str
    stance: str
    label: str
    quote_span: QuoteSpan


class BundleAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = BundleRepository(session)

    async def materialize_document_bundle(
        self,
        *,
        document: Document,
        quote_spans: list[QuoteSpan],
    ) -> None:
        if document.matter_id is None:
            return

        await self.repository.clear_document_artifacts(document.id)
        entity_keys: set[tuple[str, str, int]] = set()
        exhibit_keys: set[tuple[str, int]] = set()

        for quote_span in sorted(quote_spans, key=lambda item: item.paragraph_start):
            for entity_type, label in self._extract_entities(quote_span.text):
                normalized_label = self._normalize_label(label)
                entity_key = (entity_type.value, normalized_label, quote_span.paragraph_start)
                if entity_key in entity_keys:
                    continue
                entity_keys.add(entity_key)
                self.session.add(
                    DocumentEntity(
                        matter_id=document.matter_id,
                        document_id=document.id,
                        quote_span_id=quote_span.id,
                        entity_type=entity_type,
                        label=label,
                        normalized_label=normalized_label,
                        paragraph_start=quote_span.paragraph_start,
                        paragraph_end=quote_span.paragraph_end,
                        page_start=quote_span.page_start,
                        page_end=quote_span.page_end,
                    )
                )

            for event_date in self._extract_dates(quote_span.text):
                self.session.add(
                    ChronologyEvent(
                        matter_id=document.matter_id,
                        document_id=document.id,
                        quote_span_id=quote_span.id,
                        event_date=event_date,
                        title=self._event_title(quote_span.text),
                        summary=self._truncate(quote_span.text),
                        actor_label=self._primary_actor(quote_span.text),
                        confidence=0.92,
                    )
                )

            for exhibit_label in self._extract_exhibits(quote_span.text):
                exhibit_key = (exhibit_label, quote_span.paragraph_start)
                if exhibit_key in exhibit_keys:
                    continue
                exhibit_keys.add(exhibit_key)
                self.session.add(
                    ExhibitReference(
                        matter_id=document.matter_id,
                        document_id=document.id,
                        quote_span_id=quote_span.id,
                        label=exhibit_label,
                        normalized_label=self._normalize_label(exhibit_label),
                        context_text=self._truncate(quote_span.text),
                    )
                )

        await self.session.flush()

    async def rebuild_matter_bundle(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> None:
        snapshot = await self.repository.load_snapshot(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        await self.repository.clear_matter_relations(matter_id)

        documents = [
            item for item in snapshot.documents if item.processing_status == ProcessingStatus.READY
        ]
        spans_by_document: dict[UUID, list[QuoteSpan]] = defaultdict(list)
        for quote_span in snapshot.quote_spans:
            spans_by_document[quote_span.document_id].append(quote_span)

        relation_keys: set[tuple[str, UUID, UUID, str]] = set()
        for left_document, right_document in combinations(documents, 2):
            duplicate = self._detect_duplicate(left_document, right_document)
            if duplicate is not None:
                self.session.add(duplicate)

            for relation in self._detect_contradictions(
                matter_id=matter_id,
                left_document=left_document,
                right_document=right_document,
                left_spans=spans_by_document[left_document.id],
                right_spans=spans_by_document[right_document.id],
            ):
                key = (
                    relation.label,
                    relation.left_document_id,
                    relation.right_document_id,
                    relation.fingerprint or "",
                )
                if key in relation_keys:
                    continue
                relation_keys.add(key)
                self.session.add(relation)

        await self.session.flush()

    async def get_matter_bundle(
        self,
        *,
        matter_id: UUID,
        organization_id: UUID,
    ) -> BundleMapResponse:
        snapshot = await self.repository.load_snapshot(
            matter_id=matter_id,
            organization_id=organization_id,
        )
        if not snapshot.documents:
            raise ValueError("Matter bundle not found")

        documents = snapshot.documents
        document_map = {item.id: item for item in documents}
        quote_span_map = {item.id: item for item in snapshot.quote_spans}

        matter_entity = next((item.matter for item in documents if item.matter is not None), None)
        if matter_entity is None:
            raise ValueError("Matter bundle is missing matter metadata")

        chronology = [
            BundleChronologyItemResponse(
                id=event.id,
                date=event.event_date,
                title=event.title,
                summary=event.summary,
                source_title=document_map[event.document_id].title,
                source_type=document_map[event.document_id].source_type,
                anchor_label=self._anchor_label(event.quote_span_id, quote_span_map),
                confidence=event.confidence,
            )
            for event in snapshot.chronology
        ]

        contradiction_rows = [
            item for item in snapshot.relations if item.relation_type == RelationType.CONTRADICTION
        ]
        contradiction_rows.sort(
            key=lambda item: SEVERITY_ORDER.get(item.severity or RelationSeverity.LOW, 99)
        )
        contradictions = [
            BundleContradictionResponse(
                id=relation.id,
                issue=self._issue_label(relation.label),
                severity=(relation.severity or RelationSeverity.LOW).value,
                summary=relation.description,
                contradiction_kind=relation.label,
                source_a=document_map[relation.left_document_id].title,
                source_b=document_map[relation.right_document_id].title,
                source_a_label=self._anchor_label(relation.left_quote_span_id, quote_span_map),
                source_b_label=self._anchor_label(relation.right_quote_span_id, quote_span_map),
                source_a_type=document_map[relation.left_document_id].source_type,
                source_b_type=document_map[relation.right_document_id].source_type,
            )
            for relation in contradiction_rows
        ]

        duplicate_groups = [
            BundleDuplicateGroupResponse(
                id=relation.fingerprint or str(relation.id),
                canonical_title=document_map[relation.left_document_id].title,
                duplicate_count=2,
                reason=relation.description,
                source_type=document_map[relation.left_document_id].source_type,
                members=[
                    BundleDuplicateMemberResponse(
                        id=document_map[relation.left_document_id].id,
                        title=document_map[relation.left_document_id].title,
                        anchor_label="Checksum match",
                    ),
                    BundleDuplicateMemberResponse(
                        id=document_map[relation.right_document_id].id,
                        title=document_map[relation.right_document_id].title,
                        anchor_label="Checksum match",
                    ),
                ],
            )
            for relation in snapshot.relations
            if relation.relation_type == RelationType.DUPLICATE
        ]

        exhibit_links = [
            BundleExhibitLinkResponse(
                id=exhibit.id,
                exhibit_label=exhibit.label,
                title=document_map[exhibit.document_id].title,
                source_type=document_map[exhibit.document_id].source_type,
                anchor_label=self._anchor_label(exhibit.quote_span_id, quote_span_map),
                target_title=exhibit.label,
                note=exhibit.context_text,
            )
            for exhibit in snapshot.exhibits
        ]

        timestamps = [
            item
            for document in documents
            for item in (
                document.processing_started_at,
                document.processing_completed_at,
                document.updated_at,
            )
            if item is not None
        ]
        last_updated_at = max(timestamps) if timestamps else datetime.now(UTC)
        status_counter = Counter(document.processing_status for document in documents)

        return BundleMapResponse(
            matter_id=matter_id,
            matter_title=matter_entity.title,
            matter_reference_code=matter_entity.reference_code,
            forum=matter_entity.forum,
            stage=matter_entity.stage,
            matter_status=matter_entity.status,
            ingestion=BundleProcessingOverviewResponse(
                overall_status=self._overall_status(status_counter),
                total_documents=len(documents),
                processed_documents=status_counter[ProcessingStatus.READY]
                + status_counter[ProcessingStatus.FAILED],
                ready_documents=status_counter[ProcessingStatus.READY],
                failed_documents=status_counter[ProcessingStatus.FAILED],
                processing_documents=status_counter[ProcessingStatus.PROCESSING],
                queued_documents=status_counter[ProcessingStatus.QUEUED],
                last_updated_at=last_updated_at,
                stages=[
                    BundleProcessingStageResponse(
                        label="Queued",
                        status=ProcessingStatus.QUEUED,
                        count=status_counter[ProcessingStatus.QUEUED],
                    ),
                    BundleProcessingStageResponse(
                        label="Processing",
                        status=ProcessingStatus.PROCESSING,
                        count=status_counter[ProcessingStatus.PROCESSING],
                    ),
                    BundleProcessingStageResponse(
                        label="Ready",
                        status=ProcessingStatus.READY,
                        count=status_counter[ProcessingStatus.READY],
                    ),
                    BundleProcessingStageResponse(
                        label="Failed",
                        status=ProcessingStatus.FAILED,
                        count=status_counter[ProcessingStatus.FAILED],
                    ),
                ],
            ),
            chronology=chronology,
            contradictions=contradictions,
            clusters=self._build_clusters(documents, snapshot.entities, snapshot.exhibits),
            duplicate_groups=duplicate_groups,
            exhibit_links=exhibit_links,
            documents=[
                BundleDocumentSummaryResponse(
                    id=document.id,
                    title=document.title,
                    source_type=document.source_type,
                    processing_status=document.processing_status,
                    legal_issue=document.legal_issue,
                    created_at=document.created_at,
                    processing_stage=self._processing_stage_label(document.processing_status),
                    processing_progress=self._processing_progress(document.processing_status),
                    processing_error=document.processing_error,
                )
                for document in documents
            ],
        )

    def _build_clusters(
        self,
        documents: list[Document],
        entities: list[DocumentEntity],
        exhibits: list[ExhibitReference],
    ) -> list[BundleClusterResponse]:
        clusters: list[BundleClusterResponse] = []
        document_map = {item.id: item for item in documents}

        source_groups: dict[str, list[Document]] = defaultdict(list)
        issue_groups: dict[str, list[Document]] = defaultdict(list)
        for document in documents:
            source_groups[document.source_type.value].append(document)
            if document.legal_issue:
                issue_groups[document.legal_issue].append(document)

        for label, grouped_documents in sorted(source_groups.items()):
            clusters.append(
                self._cluster_response(
                    cluster_id=f"source:{label}",
                    cluster_type="source_type",
                    label=label.replace("_", " ").title(),
                    description="Documents grouped by source-role classification.",
                    documents=grouped_documents,
                    dominant_issue=self._dominant_issue(grouped_documents),
                )
            )

        for label, grouped_documents in sorted(
            issue_groups.items(),
            key=lambda item: (-len(item[1]), item[0]),
        ):
            clusters.append(
                self._cluster_response(
                    cluster_id=f"issue:{self._normalize_label(label)}",
                    cluster_type="issue",
                    label=label,
                    description=f"Documents grouped around the issue '{label}'.",
                    documents=grouped_documents,
                    dominant_issue=label,
                )
            )

        entity_documents: dict[str, dict[UUID, Document]] = defaultdict(dict)
        entity_meta: dict[str, tuple[str, EntityType]] = {}
        for entity in entities:
            matched_document = document_map.get(entity.document_id)
            if matched_document is None:
                continue
            entity_documents[entity.normalized_label][entity.document_id] = matched_document
            entity_meta.setdefault(entity.normalized_label, (entity.label, entity.entity_type))

        for exhibit in exhibits:
            matched_document = document_map.get(exhibit.document_id)
            if matched_document is None:
                continue
            entity_documents[exhibit.normalized_label][exhibit.document_id] = matched_document
            entity_meta.setdefault(exhibit.normalized_label, (exhibit.label, EntityType.EXHIBIT))

        for normalized_label, grouped_entity_documents in sorted(
            entity_documents.items(),
            key=lambda item: (-len(item[1]), item[0]),
        ):
            if len(grouped_entity_documents) < 2:
                continue
            label, entity_type = entity_meta[normalized_label]
            docs = list(grouped_entity_documents.values())
            cluster_type = (
                "document_ref" if entity_type == EntityType.EXHIBIT else entity_type.value
            )
            clusters.append(
                self._cluster_response(
                    cluster_id=f"entity:{normalized_label}",
                    cluster_type=cluster_type,
                    label=label,
                    description=f"Documents linked by the shared {entity_type.value} '{label}'.",
                    documents=docs,
                    dominant_issue=self._dominant_issue(docs),
                )
            )

        return clusters[:12]

    def _cluster_response(
        self,
        *,
        cluster_id: str,
        cluster_type: str,
        label: str,
        description: str,
        documents: list[Document],
        dominant_issue: str,
    ) -> BundleClusterResponse:
        source_type = Counter(item.source_type for item in documents).most_common(1)[0][0]
        if any(item.processing_status == ProcessingStatus.FAILED for item in documents):
            status = "blocked"
        elif any(item.processing_status != ProcessingStatus.READY for item in documents):
            status = "needs_review"
        else:
            status = "verified"
        return BundleClusterResponse(
            id=cluster_id,
            cluster_type=cluster_type,
            label=label,
            description=description,
            document_count=len(documents),
            dominant_issue=dominant_issue,
            source_type=source_type,
            status=status,
        )

    @staticmethod
    def _dominant_issue(documents: list[Document]) -> str:
        return Counter(
            item.legal_issue or "bundle review" for item in documents
        ).most_common(1)[0][0]

    def _extract_entities(self, text: str) -> list[tuple[EntityType, str]]:
        entities: list[tuple[EntityType, str]] = []
        lower_text = text.lower()
        for lower_label, display_label in ROLE_LABELS.items():
            if lower_label in lower_text:
                entity_type = EntityType.ORGANIZATION if lower_label == "state" else EntityType.ROLE
                entities.append((entity_type, display_label))
        for label, patterns in EXHIBIT_PATTERNS.items():
            if any(pattern in lower_text for pattern in patterns):
                entities.append((EntityType.EXHIBIT, label))
        for match in PROPER_NOUN_PATTERN.findall(text):
            if match in {"March", "India", "Constitution"}:
                continue
            entities.append((EntityType.PERSON, match))
        return entities

    def _extract_dates(self, text: str) -> list[date]:
        extracted_dates: list[date] = []
        for raw_date in DATE_PATTERN.findall(text):
            try:
                extracted_dates.append(datetime.strptime(raw_date, "%d %B %Y").date())
            except ValueError:
                continue
        return extracted_dates

    def _extract_exhibits(self, text: str) -> list[str]:
        lower_text = text.lower()
        return [
            label
            for label, patterns in EXHIBIT_PATTERNS.items()
            if any(pattern in lower_text for pattern in patterns)
        ]

    def _event_title(self, text: str) -> str:
        lower_text = text.lower()
        if "custody" in lower_text or "arrest" in lower_text or "detention" in lower_text:
            return "Custody and detention event"
        if "production" in lower_text or "remand" in lower_text or "magistrate" in lower_text:
            return "Production and remand event"
        if "counsel" in lower_text or "lawyer" in lower_text or "legal aid" in lower_text:
            return "Counsel access event"
        return self._truncate(text, limit=96)

    def _primary_actor(self, text: str) -> str | None:
        for entity_type, label in self._extract_entities(text):
            if entity_type in {EntityType.PERSON, EntityType.ORGANIZATION, EntityType.ROLE}:
                return label
        return None

    def _detect_duplicate(
        self,
        left_document: Document,
        right_document: Document,
    ) -> DocumentRelation | None:
        left_text = self._normalize_blob(left_document.extracted_text or "")
        right_text = self._normalize_blob(right_document.extracted_text or "")
        if not left_text or not right_text:
            return None

        similarity = (
            1.0
            if left_document.sha256 == right_document.sha256
            else SequenceMatcher(a=left_text[:4000], b=right_text[:4000]).ratio()
        )
        if similarity < 0.96:
            return None

        if left_document.matter_id is None:
            return None

        return DocumentRelation(
            matter_id=left_document.matter_id,
            relation_type=RelationType.DUPLICATE,
            severity=RelationSeverity.LOW,
            left_document_id=left_document.id,
            right_document_id=right_document.id,
            left_quote_span_id=None,
            right_quote_span_id=None,
            fingerprint=":".join(sorted((left_document.sha256, right_document.sha256))),
            label="Near-duplicate document pair",
            description=(
                f"{left_document.title} and {right_document.title} share materially "
                "identical text."
            ),
            confidence=round(similarity, 3),
        )

    def _detect_contradictions(
        self,
        *,
        matter_id: UUID,
        left_document: Document,
        right_document: Document,
        left_spans: list[QuoteSpan],
        right_spans: list[QuoteSpan],
    ) -> list[DocumentRelation]:
        left_signals = self._extract_claim_signals(left_spans)
        right_signals = self._extract_claim_signals(right_spans)
        relations: list[DocumentRelation] = []
        seen: set[str] = set()

        for left_signal in left_signals:
            for right_signal in right_signals:
                conflict = self._classify_conflict(left_signal, right_signal)
                if conflict is None:
                    continue
                label, description, severity, confidence = conflict
                fingerprint = (
                    f"{min(left_document.id, right_document.id)}:"
                    f"{max(left_document.id, right_document.id)}:"
                    f"{left_signal.topic}:"
                    f"{left_signal.stance}:"
                    f"{right_signal.stance}"
                )
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                relations.append(
                    DocumentRelation(
                        matter_id=matter_id,
                        relation_type=RelationType.CONTRADICTION,
                        severity=severity,
                        left_document_id=left_document.id,
                        right_document_id=right_document.id,
                        left_quote_span_id=left_signal.quote_span.id,
                        right_quote_span_id=right_signal.quote_span.id,
                        fingerprint=fingerprint,
                        label=label,
                        description=description,
                        confidence=confidence,
                    )
                )
        return relations

    def _extract_claim_signals(self, quote_spans: list[QuoteSpan]) -> list[ClaimSignal]:
        signals: list[ClaimSignal] = []
        for quote_span in quote_spans:
            lower_text = quote_span.text.lower()
            if "all formal steps were taken" in lower_text or "reflects compliance" in lower_text:
                signals.append(
                    ClaimSignal(
                        topic="procedural_compliance",
                        stance="affirmed",
                        label="Procedural compliance asserted",
                        quote_span=quote_span,
                    )
                )
            if (
                "does not reflect the actual" in lower_text
                or "no family intimation time is recorded" in lower_text
            ):
                signals.append(
                    ClaimSignal(
                        topic="record_gap",
                        stance="missing",
                        label="Record gap identified",
                        quote_span=quote_span,
                    )
                )
            if "no endorsement" in lower_text and (
                "free legal aid was offered" in lower_text or "requested counsel" in lower_text
            ):
                signals.append(
                    ClaimSignal(
                        topic="legal_aid_offer",
                        stance="missing_record",
                        label="Legal-aid offer missing from record",
                        quote_span=quote_span,
                    )
                )
            if "not permitted to speak with" in lower_text and (
                "lawyer" in lower_text or "counsel" in lower_text
            ):
                signals.append(
                    ClaimSignal(
                        topic="counsel_access",
                        stance="denied",
                        label="Counsel access denied",
                        quote_span=quote_span,
                    )
                )
            if "counsel was offered" in lower_text or "delay in securing counsel" in lower_text:
                signals.append(
                    ClaimSignal(
                        topic="counsel_access",
                        stance="affirmed",
                        label="Counsel access asserted",
                        quote_span=quote_span,
                    )
                )
            if "relative was informed" in lower_text or "family was informed" in lower_text:
                signals.append(
                    ClaimSignal(
                        topic="family_informed",
                        stance="affirmed",
                        label="Family informed",
                        quote_span=quote_span,
                    )
                )
            if "not permitted to speak with her family" in lower_text:
                signals.append(
                    ClaimSignal(
                        topic="family_informed",
                        stance="denied",
                        label="Family contact denied",
                        quote_span=quote_span,
                    )
                )
        return signals

    def _classify_conflict(
        self,
        left_signal: ClaimSignal,
        right_signal: ClaimSignal,
    ) -> tuple[str, str, RelationSeverity, float] | None:
        if left_signal.topic == right_signal.topic and left_signal.stance != right_signal.stance:
            return (
                f"{left_signal.label} is contested across the bundle",
                (
                    f"One source says '{left_signal.label.lower()}', while the paired source "
                    "records a materially inconsistent position."
                ),
                RelationSeverity.HIGH,
                0.86,
            )

        cross_topic_pairs: dict[
            tuple[str, str],
            tuple[str, str, RelationSeverity, float],
        ] = {
            (
                "procedural_compliance",
                "record_gap",
            ): (
                "Procedural compliance conflicts with record gaps",
                "One source says formal compliance was complete, while the paired source "
                "identifies record gaps.",
                RelationSeverity.HIGH,
                0.84,
            ),
            (
                "procedural_compliance",
                "legal_aid_offer",
            ): (
                "Procedural compliance conflicts with legal-aid record gaps",
                "One source says formal compliance was complete, while the paired source "
                "says the record does not show whether legal aid was offered.",
                RelationSeverity.HIGH,
                0.88,
            ),
            (
                "procedural_compliance",
                "counsel_access",
            ): (
                "Procedural compliance conflicts with counsel-access concerns",
                "One source says formal compliance was complete, while the paired source "
                "records denial or delay of access to counsel.",
                RelationSeverity.MEDIUM,
                0.8,
            ),
        }

        key = (left_signal.topic, right_signal.topic)
        if key in cross_topic_pairs and left_signal.stance == "affirmed":
            return cross_topic_pairs[key]
        reverse_key = (right_signal.topic, left_signal.topic)
        if reverse_key in cross_topic_pairs and right_signal.stance == "affirmed":
            return cross_topic_pairs[reverse_key]
        return None

    @staticmethod
    def _issue_label(label: str) -> str:
        lowered = label.lower()
        if "counsel" in lowered or "legal-aid" in lowered:
            return "Counsel access"
        if "family" in lowered:
            return "Family notice"
        if "record" in lowered:
            return "Record completeness"
        return label

    @staticmethod
    def _anchor_label(
        quote_span_id: UUID | None,
        quote_span_map: dict[UUID, QuoteSpan],
    ) -> str:
        if quote_span_id and quote_span_id in quote_span_map:
            return quote_span_map[quote_span_id].anchor_label
        return "Bundle reference"

    @staticmethod
    def _normalize_label(label: str) -> str:
        return WHITESPACE_PATTERN.sub(" ", label.strip().lower())

    @staticmethod
    def _normalize_blob(text: str) -> str:
        return WHITESPACE_PATTERN.sub(" ", text.strip().lower())

    @staticmethod
    def _truncate(text: str, limit: int = 180) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 1].rstrip() + "..."

    @staticmethod
    def _overall_status(counter: Counter[ProcessingStatus]) -> ProcessingStatus:
        if counter[ProcessingStatus.PROCESSING]:
            return ProcessingStatus.PROCESSING
        if counter[ProcessingStatus.QUEUED]:
            return ProcessingStatus.QUEUED
        if counter[ProcessingStatus.FAILED] and not counter[ProcessingStatus.READY]:
            return ProcessingStatus.FAILED
        return ProcessingStatus.READY

    @staticmethod
    def _processing_stage_label(status: ProcessingStatus) -> str:
        return status.value

    @staticmethod
    def _processing_progress(status: ProcessingStatus) -> int:
        return {
            ProcessingStatus.QUEUED: 5,
            ProcessingStatus.PROCESSING: 60,
            ProcessingStatus.READY: 100,
            ProcessingStatus.FAILED: 100,
        }[status]
