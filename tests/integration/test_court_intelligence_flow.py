from __future__ import annotations

from pathlib import Path

import pytest
from app.domain.matter import Matter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _get_matter_id(db_session: AsyncSession) -> str:
    matter = (await db_session.execute(select(Matter).limit(1))).scalar_one()
    return str(matter.id)


@pytest.mark.asyncio
async def test_public_court_import_builds_memories_profiles_and_hybrid_search(
    test_client,
    db_session: AsyncSession,
) -> None:
    matter_id = await _get_matter_id(db_session)
    case_history = Path("tests/fixtures/public_court/district_ecourts_case_history.html")
    cause_list = Path("tests/fixtures/public_court/district_ecourts_cause_list.html")

    import_response = await test_client.post(
        f"/api/v1/matters/{matter_id}/external-cases/import",
        data={
            "source_system": "district_ecourts",
            "artifact_kind": "case_history",
        },
        files={
            "file": (
                case_history.name,
                case_history.read_bytes(),
                "text/html",
            )
        },
    )
    assert import_response.status_code == 200
    external_case = import_response.json()
    assert external_case["case_number"] == "W.P.(Crl.) 1542/2026"
    assert external_case["cnr_number"] == "DLHC01015422026"
    assert external_case["judge_id"]
    assert external_case["court_id"]

    cause_list_response = await test_client.post(
        f"/api/v1/matters/{matter_id}/external-cases/import",
        data={
            "source_system": "district_ecourts",
            "artifact_kind": "cause_list",
            "external_case_id": external_case["id"],
        },
        files={
            "file": (
                cause_list.name,
                cause_list.read_bytes(),
                "text/html",
            )
        },
    )
    assert cause_list_response.status_code == 200

    list_response = await test_client.get(f"/api/v1/matters/{matter_id}/external-cases")
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["case_number"] == external_case["case_number"]

    chronology_response = await test_client.get(f"/api/v1/matters/{matter_id}/chronology")
    assert chronology_response.status_code == 200
    chronology_payload = chronology_response.json()
    assert any(item["source_kind"] == "external_case_event" for item in chronology_payload)
    assert any(item["title"] == "Matter adjourned" for item in chronology_payload)

    hearing_delta_response = await test_client.get(f"/api/v1/matters/{matter_id}/hearing-delta")
    assert hearing_delta_response.status_code == 200
    hearing_delta = hearing_delta_response.json()
    assert hearing_delta["changed_items"]

    filings_response = await test_client.get(f"/api/v1/matters/{matter_id}/filing-lineage")
    assert filings_response.status_code == 200
    filings = filings_response.json()
    assert len(filings) >= 2
    assert filings[0]["reliefs_sought"]
    assert "Family denied meeting" in filings[1]["denials"]

    parties_response = await test_client.get(
        f"/api/v1/external-cases/{external_case['id']}/parties"
    )
    assert parties_response.status_code == 200
    parties = parties_response.json()
    assert len(parties) == 2

    party_memory_response = await test_client.get(
        f"/api/v1/parties/{parties[0]['party_id']}/memory"
    )
    assert party_memory_response.status_code == 200
    party_memory = party_memory_response.json()
    assert "Litigant Memory" in party_memory["markdown_content"]
    assert party_memory["source_refs"]

    case_memory_response = await test_client.get(
        f"/api/v1/external-cases/{external_case['id']}/memory"
    )
    assert case_memory_response.status_code == 200
    case_memory = case_memory_response.json()
    assert "Case Memory" in case_memory["markdown_content"]
    assert "Next Actionable Step" in case_memory["markdown_content"]

    judge_profile_response = await test_client.get(
        f"/api/v1/judges/{external_case['judge_id']}/profile"
    )
    assert judge_profile_response.status_code == 200
    judge_profile = judge_profile_response.json()
    assert judge_profile["sample_size"] >= 1
    assert judge_profile["metrics"]["hearing_load"] >= 1

    court_profile_response = await test_client.get(
        f"/api/v1/courts/{external_case['court_id']}/profile"
    )
    assert court_profile_response.status_code == 200
    court_profile = court_profile_response.json()
    assert court_profile["sample_size"] >= 1

    search_response = await test_client.get(
        "/api/v1/search/hybrid",
        params={"q": "production delay family meeting", "matter_id": matter_id},
    )
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert search_payload["total"] >= 1
    assert any(
        item["entity_kind"] in {"case_filing", "case_memory", "document"}
        for item in search_payload["items"]
    )

    connected_response = await test_client.get(
        "/api/v1/search/connected-matters",
        params={"matter_id": matter_id},
    )
    assert connected_response.status_code == 200
    connected_payload = connected_response.json()
    assert connected_payload

    refresh_response = await test_client.post(
        f"/api/v1/external-cases/{external_case['id']}/memory/refresh",
        params={"matter_id": matter_id},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["status"] == "succeeded"
