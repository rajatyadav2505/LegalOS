from __future__ import annotations

from bs4 import BeautifulSoup

from app.domain.enums import ArtifactKind, EventType, FilingSide, PartyRole, SourceSystem
from app.integrations.indian_courts.base import (
    BaseCourtConnector,
    find_by_data_field,
    parse_optional_date,
    text_of,
)
from app.integrations.indian_courts.models import (
    ImportedArtifact,
    ImportedCaseData,
    ImportedConnectedCase,
    ImportedCounsel,
    ImportedDeadline,
    ImportedEvent,
    ImportedFiling,
    ImportedIdentifier,
    ImportedListing,
    ImportedParty,
)

EVENT_TYPE_MAP = {
    "filing_submitted": EventType.FILING_SUBMITTED,
    "filing_defect": EventType.FILING_DEFECT,
    "filing_cured": EventType.FILING_CURED,
    "listed": EventType.LISTED,
    "heard": EventType.HEARD,
    "adjourned": EventType.ADJOURNED,
    "order_uploaded": EventType.ORDER_UPLOADED,
    "judgment_uploaded": EventType.JUDGMENT_UPLOADED,
    "notice_issued": EventType.NOTICE_ISSUED,
    "service_completed": EventType.SERVICE_COMPLETED,
    "caveat_found": EventType.CAVEAT_FOUND,
    "office_report_added": EventType.OFFICE_REPORT_ADDED,
    "compliance_due": EventType.COMPLIANCE_DUE,
    "compliance_filed": EventType.COMPLIANCE_FILED,
    "disposed": EventType.DISPOSED,
    "restored": EventType.RESTORED,
    "transferred": EventType.TRANSFERRED,
}

PARTY_ROLE_MAP = {
    "petitioner": PartyRole.PETITIONER,
    "respondent": PartyRole.RESPONDENT,
    "appellant": PartyRole.APPELLANT,
    "appellee": PartyRole.APPELLEE,
    "applicant": PartyRole.APPLICANT,
    "plaintiff": PartyRole.PLAINTIFF,
    "defendant": PartyRole.DEFENDANT,
    "caveator": PartyRole.CAVEATOR,
    "intervenor": PartyRole.INTERVENOR,
}

FILING_SIDE_MAP = {
    "petitioner": FilingSide.PETITIONER,
    "respondent": FilingSide.RESPONDENT,
    "appellant": FilingSide.APPELLANT,
    "appellee": FilingSide.APPELLEE,
    "applicant": FilingSide.APPLICANT,
    "caveator": FilingSide.CAVEATOR,
    "registry": FilingSide.REGISTRY,
    "court": FilingSide.COURT,
}


def _attr_text(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return str(value[0]) if value else None
    return str(value)


class DistrictECourtsConnector(BaseCourtConnector):
    source_system = SourceSystem.DISTRICT_ECOURTS

    def supports(self, artifact_kind: ArtifactKind, content_type: str, text: str) -> bool:
        return "data-legalos-source=\"district-ecourts\"" in text or (
            artifact_kind in {ArtifactKind.CASE_HISTORY, ArtifactKind.CAUSE_LIST}
            and "district ecourts" in text.lower()
        )

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
        soup = BeautifulSoup(raw_text, "html.parser")
        title = find_by_data_field(soup, "case_title") or "Imported external case"
        case_number = find_by_data_field(soup, "case_number") or "Unknown case number"
        court_name = find_by_data_field(soup, "court_name") or "Unknown court"
        payload = self.build_base_case(
            artifact_kind=artifact_kind,
            title=title,
            case_number=case_number,
            court_name=court_name,
            content_hash=content_hash,
            source_url=source_url,
            observed_at=observed_at,
        )
        payload.update(
            {
                "cnr_number": find_by_data_field(soup, "cnr_number"),
                "case_type": find_by_data_field(soup, "case_type"),
                "filing_number": find_by_data_field(soup, "filing_number"),
                "filing_date": parse_optional_date(find_by_data_field(soup, "filing_date")),
                "registration_date": parse_optional_date(
                    find_by_data_field(soup, "registration_date")
                ),
                "status_text": find_by_data_field(soup, "status_text"),
                "subject": find_by_data_field(soup, "subject"),
                "latest_stage": find_by_data_field(soup, "latest_stage"),
                "next_listing_date": parse_optional_date(
                    find_by_data_field(soup, "next_listing_date")
                ),
                "establishment_name": find_by_data_field(soup, "establishment_name"),
                "establishment_code": find_by_data_field(soup, "establishment_code"),
                "district_name": find_by_data_field(soup, "district_name"),
                "state_name": find_by_data_field(soup, "state_name"),
                "bench_label": find_by_data_field(soup, "bench_label"),
                "court_hall": find_by_data_field(soup, "court_hall"),
                "judge_name": find_by_data_field(soup, "judge_name"),
                "identifiers": self._parse_identifiers(soup),
                "parties": self._parse_parties(soup),
                "counsels": self._parse_counsels(soup),
                "events": self._parse_events(soup),
                "listings": self._parse_listings(soup),
                "filings": self._parse_filings(soup),
                "deadlines": self._parse_deadlines(soup),
                "artifacts": self._parse_artifacts(soup, artifact_kind=artifact_kind),
                "connected_cases": self._parse_connected_cases(soup),
            }
        )
        return ImportedCaseData.model_validate(payload)

    def _parse_identifiers(self, soup: BeautifulSoup) -> list[ImportedIdentifier]:
        identifiers: list[ImportedIdentifier] = []
        for field, primary in (
            ("cnr_number", True),
            ("case_number", False),
            ("filing_number", False),
        ):
            value = find_by_data_field(soup, field)
            if value:
                identifiers.append(
                    ImportedIdentifier(
                        identifier_type=field,
                        identifier_value=value,
                        is_primary=primary,
                    )
                )
        return identifiers

    def _parse_parties(self, soup: BeautifulSoup) -> list[ImportedParty]:
        items: list[ImportedParty] = []
        for node in soup.select("[data-list='parties'] li"):
            role_key = (_attr_text(node.get("data-role")) or "other").lower()
            display_name = text_of(node)
            if display_name is None:
                continue
            aliases = [
                alias.get_text(" ", strip=True)
                for alias in node.select("[data-alias]")
                if alias.get_text(" ", strip=True)
            ]
            items.append(
                ImportedParty(
                    role=PARTY_ROLE_MAP.get(role_key, PartyRole.OTHER),
                    display_name=display_name,
                    aliases=aliases,
                )
            )
        return items

    def _parse_counsels(self, soup: BeautifulSoup) -> list[ImportedCounsel]:
        items: list[ImportedCounsel] = []
        for node in soup.select("[data-list='counsels'] li"):
            counsel_name = text_of(node)
            if counsel_name is None:
                continue
            aliases = [
                alias.get_text(" ", strip=True)
                for alias in node.select("[data-alias]")
                if alias.get_text(" ", strip=True)
            ]
            items.append(
                ImportedCounsel(
                    counsel_name=counsel_name,
                    side_label=_attr_text(node.get("data-side")),
                    aliases=aliases,
                )
            )
        return items

    def _parse_events(self, soup: BeautifulSoup) -> list[ImportedEvent]:
        items: list[ImportedEvent] = []
        for row in soup.select("[data-table='events'] tr[data-event-type]"):
            event_date = parse_optional_date(_attr_text(row.get("data-event-date")))
            title = text_of(row.select_one("[data-col='title']"))
            description = text_of(row.select_one("[data-col='detail']"))
            if event_date is None or title is None or description is None:
                continue
            event_key = (_attr_text(row.get("data-event-type")) or "listed").lower()
            items.append(
                ImportedEvent(
                    event_type=EVENT_TYPE_MAP.get(event_key, EventType.LISTED),
                    event_date=event_date,
                    title=title,
                    description=description,
                    source_anchor=_attr_text(row.get("data-anchor")),
                    judge_name=text_of(row.select_one("[data-col='judge']")),
                )
            )
        return items

    def _parse_listings(self, soup: BeautifulSoup) -> list[ImportedListing]:
        items: list[ImportedListing] = []
        for row in soup.select("[data-table='listings'] tr[data-listing-date]"):
            listing_date = parse_optional_date(_attr_text(row.get("data-listing-date")))
            if listing_date is None:
                continue
            items.append(
                ImportedListing(
                    listing_date=listing_date,
                    purpose=text_of(row.select_one("[data-col='purpose']")),
                    item_number=text_of(row.select_one("[data-col='item_number']")),
                    bench_label=text_of(row.select_one("[data-col='bench']")),
                    court_hall=text_of(row.select_one("[data-col='court_hall']")),
                    judge_name=text_of(row.select_one("[data-col='judge']")),
                )
            )
        return items

    def _parse_filings(self, soup: BeautifulSoup) -> list[ImportedFiling]:
        items: list[ImportedFiling] = []
        for row in soup.select("[data-table='filings'] tr[data-filing-type]"):
            filing_type = _attr_text(row.get("data-filing-type"))
            title = text_of(row.select_one("[data-col='title']"))
            if filing_type is None or title is None:
                continue
            side_key = (_attr_text(row.get("data-side")) or "unknown").lower()
            items.append(
                ImportedFiling(
                    filing_side=FILING_SIDE_MAP.get(side_key, FilingSide.UNKNOWN),
                    filing_type=filing_type,
                    title=title,
                    filing_date=parse_optional_date(_attr_text(row.get("data-filing-date"))),
                    reliefs_sought=self._split_list(
                        text_of(row.select_one("[data-col='reliefs']"))
                    ),
                    fact_assertions=self._split_list(
                        text_of(row.select_one("[data-col='facts']"))
                    ),
                    admissions=self._split_list(
                        text_of(row.select_one("[data-col='admissions']"))
                    ),
                    denials=self._split_list(text_of(row.select_one("[data-col='denials']"))),
                    annexures_relied=self._split_list(
                        text_of(row.select_one("[data-col='annexures']"))
                    ),
                    statutes_cited=self._split_list(
                        text_of(row.select_one("[data-col='statutes']"))
                    ),
                    precedents_cited=self._split_list(
                        text_of(row.select_one("[data-col='precedents']"))
                    ),
                    extracted_summary=text_of(row.select_one("[data-col='summary']")),
                )
            )
        return items

    def _parse_deadlines(self, soup: BeautifulSoup) -> list[ImportedDeadline]:
        items: list[ImportedDeadline] = []
        for row in soup.select("[data-table='deadlines'] tr[data-due-date]"):
            due_date = parse_optional_date(_attr_text(row.get("data-due-date")))
            title = text_of(row.select_one("[data-col='title']"))
            if due_date is None or title is None:
                continue
            items.append(
                ImportedDeadline(
                    due_date=due_date,
                    title=title,
                    status_text=text_of(row.select_one("[data-col='status']")),
                    detail=text_of(row.select_one("[data-col='detail']")),
                )
            )
        return items

    def _parse_artifacts(
        self,
        soup: BeautifulSoup,
        *,
        artifact_kind: ArtifactKind,
    ) -> list[ImportedArtifact]:
        items = [
            ImportedArtifact(
                artifact_kind=artifact_kind,
                title=text_of(node.select_one("[data-col='title']")) or "Imported artifact",
                summary=text_of(node.select_one("[data-col='summary']")),
                neutral_citation=text_of(node.select_one("[data-col='neutral_citation']")),
            )
            for node in soup.select("[data-table='artifacts'] tr")
        ]
        if items:
            return items
        return [ImportedArtifact(artifact_kind=artifact_kind, title="Imported docket artifact")]

    def _parse_connected_cases(self, soup: BeautifulSoup) -> list[ImportedConnectedCase]:
        items: list[ImportedConnectedCase] = []
        for row in soup.select("[data-table='connected_cases'] tr[data-case-number]"):
            case_number = _attr_text(row.get("data-case-number"))
            title = text_of(row.select_one("[data-col='title']"))
            if case_number is None or title is None:
                continue
            items.append(
                ImportedConnectedCase(
                    relation_label=_attr_text(row.get("data-relation")) or "connected",
                    case_number=case_number,
                    title=title,
                    note=text_of(row.select_one("[data-col='note']")),
                )
            )
        return items

    @staticmethod
    def _split_list(value: str | None) -> list[str]:
        if value is None:
            return []
        return [item.strip() for item in value.split("|") if item.strip()]
