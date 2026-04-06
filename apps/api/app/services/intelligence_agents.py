from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from app.domain.court_intelligence import (
    CaseMemorySnapshot,
    CourtProfileSnapshot,
    HybridIndexEntry,
    JudgeProfileSnapshot,
    LitigantMemorySnapshot,
    PublicSourceSnapshot,
)
from app.domain.enums import (
    ArtifactKind,
    ConfidenceBand,
    HybridEntityKind,
    ProfileWindow,
    SourceSystem,
    VerificationStatus,
)
from app.integrations.indian_courts import (
    DistrictECourtsConnector,
    ECourtsJudgmentsConnector,
    HighCourtServicesConnector,
    NJDGConnector,
    SupremeCourtIndiaConnector,
)
from app.integrations.indian_courts.base import slugify
from app.integrations.indian_courts.models import ImportedCaseData
from app.services.extraction import DocumentExtractor
from app.services.model_adapters import AdapterRegistry
from app.services.storage import LocalFilesystemStorage, StoredObject

CONNECTORS = (
    DistrictECourtsConnector(),
    HighCourtServicesConnector(),
    ECourtsJudgmentsConnector(),
    NJDGConnector(),
    SupremeCourtIndiaConnector(),
)
NAME_PREFIX_PATTERN = re.compile(r"^(hon'?ble|justice|dr\.?|mr\.?|mrs\.?|ms\.?)\s+", re.I)


@dataclass(slots=True)
class FetchResult:
    snapshot: PublicSourceSnapshot
    stored_object: StoredObject
    content_hash: str


class FetchAgent:
    def __init__(self) -> None:
        self.storage = LocalFilesystemStorage()

    def store_snapshot(
        self,
        *,
        organization_id: UUID,
        uploaded_by_user_id: UUID | None,
        source_system: SourceSystem,
        artifact_kind: ArtifactKind,
        file_name: str,
        content_type: str,
        payload: bytes,
        source_url: str | None,
        observed_at: datetime | None,
    ) -> FetchResult:
        content_hash = hashlib.sha256(payload).hexdigest()
        storage_key = (
            f"{organization_id}/public-snapshots/{source_system.value}/"
            f"{content_hash}-{Path(file_name).name}"
        )
        stored = self.storage.save_bytes(storage_key, payload)
        snapshot = PublicSourceSnapshot(
            organization_id=organization_id,
            uploaded_by_user_id=uploaded_by_user_id,
            source_system=source_system,
            artifact_kind=artifact_kind,
            source_url=source_url,
            observed_at=observed_at,
            fetched_at=datetime.now(UTC),
            original_file_name=file_name,
            content_type=content_type,
            storage_path=stored.relative_path,
            content_hash=content_hash,
            file_size_bytes=len(payload),
            import_method="user_supplied",
        )
        return FetchResult(snapshot=snapshot, stored_object=stored, content_hash=content_hash)


class ExtractAgent:
    def __init__(self) -> None:
        self.extractor = DocumentExtractor()

    def parse_snapshot(
        self,
        *,
        source_system: SourceSystem,
        artifact_kind: ArtifactKind,
        file_name: str,
        content_type: str,
        payload: bytes,
        content_hash: str,
        source_url: str | None,
        observed_at: datetime | None,
    ) -> ImportedCaseData:
        extracted = self.extractor.extract(
            file_name=file_name,
            content_type=content_type,
            payload=payload,
        )
        for connector in CONNECTORS:
            if connector.source_system != source_system:
                continue
            if connector.supports(artifact_kind, content_type, extracted.full_text):
                return connector.parse(
                    artifact_kind=artifact_kind,
                    content_type=content_type,
                    raw_text=extracted.full_text,
                    content_hash=content_hash,
                    source_url=source_url,
                    observed_at=observed_at,
                )
        raise ValueError("No lawful parser is available for the supplied official artifact")


class NormalizeAgent:
    @staticmethod
    def normalize_name(value: str) -> str:
        value = value.strip()
        value = NAME_PREFIX_PATTERN.sub("", value)
        return " ".join(value.lower().split())

    @staticmethod
    def slugify_court(value: str) -> str:
        return slugify(value)


class PartyResolutionAgent:
    @staticmethod
    def normalized_party_name(value: str) -> str:
        return " ".join(value.lower().replace(",", " ").split())


class QualityGuardAgent:
    def require_evidence(self, items: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
        return [(heading, lines) for heading, lines in items if lines]

    @staticmethod
    def cited_line(text: str, source_refs: list[str]) -> str:
        if not source_refs:
            raise ValueError("Unsupported assertion rejected because it lacks source references")
        return f"- {text} Sources: {', '.join(source_refs)}"


class ChronologyAgent:
    @staticmethod
    def summarize_hearing_delta(events: list[dict[str, object]]) -> dict[str, object]:
        if not events:
            return {
                "summary": "No external hearing events have been imported yet.",
                "changed_items": [],
                "latest_event_date": None,
            }
        latest = events[-1]
        previous = events[-2] if len(events) > 1 else None
        changes = [f"{latest['title']} on {latest['event_date']}"]
        if previous is not None and latest["event_date"] != previous["event_date"]:
            changes.append(f"Previous hearing record was {previous['title']} on {previous['event_date']}")
        return {
            "summary": latest["description"],
            "changed_items": changes,
            "latest_event_date": latest["event_date"],
        }


class ProfileAgent:
    @staticmethod
    def confidence_from_sample(sample_size: int) -> ConfidenceBand:
        if sample_size >= 8:
            return ConfidenceBand.HIGH
        if sample_size >= 3:
            return ConfidenceBand.MEDIUM
        return ConfidenceBand.LOW

    @staticmethod
    def metrics_markdown(metrics: dict[str, object]) -> list[str]:
        lines: list[str] = []
        for key, value in metrics.items():
            if value is None:
                continue
            label = key.replace("_", " ").title()
            lines.append(f"- {label}: {value}")
        return lines


class RetrievalAgent:
    def __init__(self) -> None:
        self.adapters = AdapterRegistry()

    def build_entries(
        self,
        *,
        organization_id: UUID,
        matter_id: UUID | None,
        external_case_id: UUID | None,
        items: list[tuple[HybridEntityKind, str, str, str, str | None, dict[str, object], UUID | None, UUID | None, UUID | None, UUID | None]],
    ) -> list[HybridIndexEntry]:
        texts = [item[3] for item in items]
        embeddings, _ = self.adapters.embed(texts)
        entries: list[HybridIndexEntry] = []
        for item, embedding in zip(items, embeddings, strict=True):
            entity_kind, source_id, title, body_text, source_anchor, metadata_json, party_id, judge_id, court_id, entry_case_id = item
            content_hash = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
            entries.append(
                HybridIndexEntry(
                    organization_id=organization_id,
                    matter_id=matter_id,
                    external_case_id=entry_case_id if entry_case_id is not None else external_case_id,
                    party_id=party_id,
                    judge_id=judge_id,
                    court_id=court_id,
                    entity_kind=entity_kind,
                    source_id=source_id,
                    title=title,
                    body_text=body_text,
                    source_anchor=source_anchor,
                    source_url=metadata_json.get("source_url") if metadata_json else None,
                    metadata_json=metadata_json,
                    embedding=embedding,
                    content_hash=content_hash,
                )
            )
        return entries

    def score(
        self,
        *,
        query: str,
        entries: list[HybridIndexEntry],
    ) -> list[tuple[HybridIndexEntry, float]]:
        query_embedding, _ = self.adapters.embed([query])
        query_vector = query_embedding[0]
        ranked: list[tuple[HybridIndexEntry, float]] = []
        for entry in entries:
            lexical = self._lexical_score(query, f"{entry.title}\n{entry.body_text}")
            semantic = self._cosine_similarity(query_vector, entry.embedding or [])
            ranked.append((entry, lexical + semantic))
        reranked, _ = self.adapters.rerank(
            query=query,
            items=[(entry.id.hex, score) for entry, score in ranked],
        )
        score_map = {item_id: score for item_id, score in reranked}
        ranked.sort(key=lambda item: score_map.get(item[0].id.hex, item[1]), reverse=True)
        return ranked

    @staticmethod
    def _lexical_score(query: str, body: str) -> float:
        tokens = {token for token in re.findall(r"[A-Za-z0-9_]+", query.lower()) if token}
        haystack = body.lower()
        return float(sum(haystack.count(token) for token in tokens))

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0
        return float(sum(a * b for a, b in zip(left, right, strict=True)))


class DraftingPlannerAgent:
    def plan_from_case_memory(self, markdown_content: str) -> dict[str, object]:
        headings = [line[3:].strip() for line in markdown_content.splitlines() if line.startswith("## ")]
        return {
            "recommended_sections": headings,
            "planning_label": "Use source-backed sections only.",
        }


class MemoryArtifactBuilder:
    def __init__(self) -> None:
        self.storage = LocalFilesystemStorage()
        self.adapters = AdapterRegistry()
        self.guard = QualityGuardAgent()

    def save_markdown(
        self,
        *,
        relative_path: str,
        title: str,
        sections: list[tuple[str, list[str]]],
    ) -> tuple[str, str]:
        guarded_sections = self.guard.require_evidence(sections)
        markdown_content, _ = self.adapters.render_markdown(title=title, sections=guarded_sections)
        stored = self.storage.save_bytes(relative_path, markdown_content.encode("utf-8"))
        return stored.relative_path, markdown_content

    def build_litigant_snapshot(
        self,
        *,
        organization_id: UUID,
        party_id: UUID,
        storage_path: str,
        markdown_content: str,
        source_refs: list[dict[str, object]],
        generated_by_job_id: UUID | None,
        confidence: ConfidenceBand,
    ) -> LitigantMemorySnapshot:
        return LitigantMemorySnapshot(
            organization_id=organization_id,
            party_id=party_id,
            generated_by_job_id=generated_by_job_id,
            storage_path=storage_path,
            markdown_content=markdown_content,
            source_refs=source_refs,
            confidence=confidence,
            verification_status=VerificationStatus.VERIFIED,
            is_current=True,
        )

    def build_case_snapshot(
        self,
        *,
        organization_id: UUID,
        external_case_id: UUID,
        matter_id: UUID | None,
        storage_path: str,
        markdown_content: str,
        source_refs: list[dict[str, object]],
        generated_by_job_id: UUID | None,
        confidence: ConfidenceBand,
    ) -> CaseMemorySnapshot:
        return CaseMemorySnapshot(
            organization_id=organization_id,
            external_case_id=external_case_id,
            matter_id=matter_id,
            generated_by_job_id=generated_by_job_id,
            storage_path=storage_path,
            markdown_content=markdown_content,
            source_refs=source_refs,
            confidence=confidence,
            verification_status=VerificationStatus.VERIFIED,
            is_current=True,
        )

    def build_judge_profile(
        self,
        *,
        organization_id: UUID,
        judge_id: UUID,
        court_id: UUID | None,
        storage_path: str,
        markdown_content: str,
        source_refs: list[dict[str, object]],
        generated_by_job_id: UUID | None,
        sample_size: int,
        freshness_timestamp: datetime | None,
        metrics: dict[str, object],
    ) -> JudgeProfileSnapshot:
        return JudgeProfileSnapshot(
            organization_id=organization_id,
            judge_id=judge_id,
            court_id=court_id,
            generated_by_job_id=generated_by_job_id,
            window=ProfileWindow.ALL_TIME,
            sample_size=sample_size,
            freshness_timestamp=freshness_timestamp,
            confidence=ProfileAgent.confidence_from_sample(sample_size),
            metrics=metrics,
            markdown_content=markdown_content,
            storage_path=storage_path,
            source_refs=source_refs,
            is_current=True,
        )

    def build_court_profile(
        self,
        *,
        organization_id: UUID,
        court_id: UUID,
        storage_path: str,
        markdown_content: str,
        source_refs: list[dict[str, object]],
        generated_by_job_id: UUID | None,
        sample_size: int,
        freshness_timestamp: datetime | None,
        metrics: dict[str, object],
    ) -> CourtProfileSnapshot:
        return CourtProfileSnapshot(
            organization_id=organization_id,
            court_id=court_id,
            generated_by_job_id=generated_by_job_id,
            window=ProfileWindow.ALL_TIME,
            sample_size=sample_size,
            freshness_timestamp=freshness_timestamp,
            confidence=ProfileAgent.confidence_from_sample(sample_size),
            metrics=metrics,
            markdown_content=markdown_content,
            storage_path=storage_path,
            source_refs=source_refs,
            is_current=True,
        )
