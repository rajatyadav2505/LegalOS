from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import UTC, date, datetime

from bs4 import BeautifulSoup, Tag

from app.domain.enums import ArtifactKind, ConfidenceBand, SourceSystem, VerificationStatus
from app.integrations.indian_courts.models import ImportedCaseData

DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d %B %Y", "%d %b %Y", "%Y-%m-%d")


def parse_optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(stripped, fmt).date()
        except ValueError:
            continue
    return None


def slugify(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-")


def text_of(node: Tag | None) -> str | None:
    if node is None:
        return None
    text = " ".join(node.get_text(" ", strip=True).split())
    return text or None


def find_by_data_field(soup: BeautifulSoup, field: str) -> str | None:
    return text_of(soup.select_one(f"[data-field='{field}']"))


class BaseCourtConnector(ABC):
    source_system: SourceSystem
    parser_version = "2026-04-07"

    @abstractmethod
    def supports(self, artifact_kind: ArtifactKind, content_type: str, text: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(
        self,
        *,
        artifact_kind: ArtifactKind,
        content_type: str,
        raw_text: str,
        content_hash: str,
        source_url: str | None,
        observed_at: datetime | None,
    ) -> ImportedCaseData:
        raise NotImplementedError

    def build_base_case(
        self,
        *,
        artifact_kind: ArtifactKind,
        title: str,
        case_number: str,
        court_name: str,
        content_hash: str,
        source_url: str | None,
        observed_at: datetime | None,
    ) -> dict[str, object]:
        return {
            "source_system": self.source_system,
            "artifact_kind": artifact_kind,
            "title": title,
            "case_number": case_number,
            "court_name": court_name,
            "source_url": source_url,
            "observed_at": observed_at,
            "fetched_at": datetime.now(UTC),
            "content_hash": content_hash,
            "parser_version": self.parser_version,
            "confidence": ConfidenceBand.MEDIUM,
            "verification_status": VerificationStatus.PARSED,
        }
