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
async def test_upload_search_save_and_export_flow(test_client, db_session: AsyncSession) -> None:
    matter_id = await _get_matter_id(db_session)

    upload_response = await test_client.post(
        "/api/v1/documents/upload",
        data={
            "matter_id": matter_id,
            "source_type": "my_document",
            "title": "Draft petition note on detention facts",
            "authority_kind": "matter_document",
            "legal_issue": "illegal detention and access to counsel",
            "defer_processing": "false",
        },
        files={
            "file": (
                "petition_note.txt",
                Path("tests/fixtures/sample_matter/petition_note.txt").read_bytes(),
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 200
    uploaded_document = upload_response.json()
    assert uploaded_document["processing_status"] == "ready"

    search_response = await test_client.get(
        "/api/v1/research/search",
        params={"matter_id": matter_id, "q": "personal liberty legal aid"},
    )
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert search_payload["total"] >= 1
    first_result = search_payload["items"][0]
    assert first_result["quote_text"]
    assert first_result["quote_checksum"]

    save_response = await test_client.post(
        f"/api/v1/research/matters/{matter_id}/saved-authorities",
        json={
            "quote_span_id": first_result["quote_span_id"],
            "citation_id": None,
            "treatment": "apply",
            "issue_label": "Custody without counsel",
            "note": "Use for the liberty and legal-aid plank."
        },
    )
    assert save_response.status_code == 200
    saved_payload = save_response.json()
    assert saved_payload["treatment"] == "apply"

    quote_response = await test_client.get(
        f"/api/v1/research/quote-spans/{first_result['quote_span_id']}"
    )
    assert quote_response.status_code == 200
    assert quote_response.json()["checksum"] == first_result["quote_checksum"]

    export_response = await test_client.get(
        f"/api/v1/research/matters/{matter_id}/export",
        params={"format": "json"},
    )
    assert export_response.status_code == 200
    export_payload = export_response.json()
    assert export_payload["file_name"].endswith(".md")
    assert "Custody without counsel" in export_payload["content"]
