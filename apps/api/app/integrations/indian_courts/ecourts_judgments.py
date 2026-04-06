from __future__ import annotations

from app.domain.enums import ArtifactKind, SourceSystem
from app.integrations.indian_courts.base import BaseCourtConnector
from app.integrations.indian_courts.district_ecourts import DistrictECourtsConnector
from app.integrations.indian_courts.models import ImportedCaseData


class ECourtsJudgmentsConnector(BaseCourtConnector):
    source_system = SourceSystem.ECOURTS_JUDGMENTS

    def supports(self, artifact_kind: ArtifactKind, content_type: str, text: str) -> bool:
        return 'data-legalos-source="ecourts-judgments"' in text

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
