from __future__ import annotations

import json
from datetime import UTC, datetime

from app.domain.enums import ArtifactKind, ConfidenceBand, SourceSystem, VerificationStatus
from app.integrations.indian_courts.base import BaseCourtConnector
from app.integrations.indian_courts.models import ImportedCaseData, ImportedIdentifier


class NJDGConnector(BaseCourtConnector):
    source_system = SourceSystem.NJDG

    def supports(self, artifact_kind: ArtifactKind, content_type: str, text: str) -> bool:
        return content_type.endswith("json") or text.strip().startswith("{")

    def parse(
        self,
        *,
        artifact_kind: ArtifactKind,
        content_type: str,
        raw_text: str,
        content_hash: str,
        source_url: str | None,
        observed_at,
    ) -> ImportedCaseData:
        payload = json.loads(raw_text)
        fetched_at = datetime.now(UTC)
        return ImportedCaseData(
            source_system=self.source_system,
            artifact_kind=artifact_kind,
            title=str(payload.get("title") or payload.get("case_title") or "NJDG import"),
            case_number=str(payload.get("case_number") or payload.get("cnr") or "Unknown"),
            cnr_number=payload.get("cnr"),
            court_name=str(payload.get("court_name") or "Unknown court"),
            district_name=payload.get("district_name"),
            state_name=payload.get("state_name"),
            source_url=source_url,
            observed_at=observed_at,
            fetched_at=fetched_at,
            content_hash=content_hash,
            parser_version=self.parser_version,
            confidence=ConfidenceBand.LOW,
            verification_status=VerificationStatus.NEEDS_REVIEW,
            identifiers=[
                ImportedIdentifier(
                    identifier_type="cnr_number",
                    identifier_value=str(payload["cnr"]),
                    is_primary=True,
                )
            ]
            if payload.get("cnr")
            else [],
        )
