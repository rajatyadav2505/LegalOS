from __future__ import annotations

from app.domain.enums import ArtifactKind, SourceSystem
from app.integrations.indian_courts.base import BaseCourtConnector
from app.integrations.indian_courts.district_ecourts import DistrictECourtsConnector
from app.integrations.indian_courts.models import ImportedCaseData


class HighCourtServicesConnector(BaseCourtConnector):
    source_system = SourceSystem.HIGH_COURT_SERVICES

    def supports(self, artifact_kind: ArtifactKind, content_type: str, text: str) -> bool:
        return 'data-legalos-source="high-court-services"' in text

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
        # The high-court exported HTML fixture uses the same normalized data-field structure
        # as the district parser, so we can keep one bounded parser path.
        return (
            DistrictECourtsConnector()
            .parse(
                artifact_kind=artifact_kind,
                content_type=content_type,
                raw_text=raw_text,
                content_hash=content_hash,
                source_url=source_url,
                observed_at=observed_at,
            )
            .model_copy(update={"source_system": self.source_system})
        )
