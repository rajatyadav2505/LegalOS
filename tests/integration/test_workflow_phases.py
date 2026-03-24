from __future__ import annotations

from pathlib import Path

import pytest
from app.domain.matter import Matter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _get_matter_id(db_session: AsyncSession) -> str:
    matter = (await db_session.execute(select(Matter).limit(1))).scalar_one()
    return str(matter.id)


async def _upload_document(
    *,
    test_client,
    matter_id: str,
    fixture_name: str,
    title: str,
    source_type: str = "my_document",
    legal_issue: str,
) -> dict[str, object]:
    response = await test_client.post(
        "/api/v1/documents/upload",
        data={
            "matter_id": matter_id,
            "source_type": source_type,
            "title": title,
            "authority_kind": "matter_document",
            "legal_issue": legal_issue,
            "process_in_background": "false",
        },
        files={
            "file": (
                fixture_name,
                Path(f"tests/fixtures/sample_matter/{fixture_name}").read_bytes(),
                "text/plain",
            )
        },
    )
    assert response.status_code == 200
    return response.json()


async def _save_verified_authority(
    *,
    test_client,
    matter_id: str,
) -> tuple[dict[str, object], dict[str, object]]:
    search_response = await test_client.get(
        "/api/v1/research/search",
        params={"matter_id": matter_id, "q": "legal aid liberty arrest safeguards"},
    )
    assert search_response.status_code == 200
    first_result = search_response.json()["items"][0]

    save_response = await test_client.post(
        f"/api/v1/research/matters/{matter_id}/saved-authorities",
        json={
            "quote_span_id": first_result["quote_span_id"],
            "citation_id": None,
            "treatment": "apply",
            "issue_label": "Custody without counsel",
            "note": "Use for the drafting and hearing-prep record.",
        },
    )
    assert save_response.status_code == 200
    return first_result, save_response.json()


async def _generate_draft(
    *,
    test_client,
    matter_id: str,
    document_type: str,
    style_pack_id: str | None = None,
    title: str | None = None,
) -> dict[str, object]:
    response = await test_client.post(
        f"/api/v1/drafting/matters/{matter_id}/documents/generate",
        json={
            "document_type": document_type,
            "title": title,
            "style_pack_id": style_pack_id,
            "annexure_document_ids": [],
            "include_saved_authorities": True,
            "include_bundle_intelligence": True,
        },
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_drafting_flow_supports_versions_placeholders_and_extended_templates(
    test_client,
    db_session: AsyncSession,
) -> None:
    matter_id = await _get_matter_id(db_session)

    uploaded = await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="petition_note.txt",
        title="Petition note on detention facts",
        legal_issue="illegal detention and access to counsel",
    )
    assert uploaded["processing_status"] == "ready"

    first_result, _saved = await _save_verified_authority(
        test_client=test_client,
        matter_id=matter_id,
    )

    first_draft = await _generate_draft(
        test_client=test_client,
        matter_id=matter_id,
        document_type="petition",
    )
    assert first_draft["document_type"] == "petition"
    assert first_draft["version_number"] == 1
    assert first_draft["authorities_used"][0]["checksum"] == first_result["quote_checksum"]
    assert any(
        "opponent" in item.lower() for item in first_draft["unresolved_placeholders"]
    )

    style_pack_response = await test_client.post(
        "/api/v1/drafting/style-packs",
        json={
            "name": "Detention Chamber Style",
            "description": "Formal chamber petition voice.",
            "tone": "measured and courtroom-facing",
            "opening_phrase": "It is respectfully shown",
            "prayer_style": "It is therefore respectfully prayed",
            "citation_style": "anchor-plus-checksum",
            "source_document_ids": [uploaded["id"]],
        },
    )
    assert style_pack_response.status_code == 200
    style_pack = style_pack_response.json()
    assert style_pack["voice_notes"]
    assert uploaded["title"] in style_pack["sample_document_titles"]

    second_draft = await _generate_draft(
        test_client=test_client,
        matter_id=matter_id,
        document_type="petition",
        style_pack_id=style_pack["id"],
        title="Styled Petition Draft",
    )
    assert second_draft["version_number"] == 2
    assert second_draft["style_pack"]["id"] == style_pack["id"]
    assert any(
        "It is respectfully shown" in section["body_text"]
        for section in second_draft["sections"]
    )

    export_response = await test_client.get(
        f"/api/v1/drafting/documents/{second_draft['id']}/export"
    )
    assert export_response.status_code == 200
    export_payload = export_response.json()
    assert export_payload["file_name"].endswith(".md")
    assert "Styled Petition Draft" in export_payload["content"]
    assert "Style pack: Detention Chamber Style" in export_payload["content"]

    redline_response = await test_client.get(
        f"/api/v1/drafting/documents/{second_draft['id']}/redline",
        params={"previous_version_id": first_draft["id"]},
    )
    assert redline_response.status_code == 200
    redline_payload = redline_response.json()
    assert redline_payload["previous_draft_id"] == first_draft["id"]
    assert any(
        "It is respectfully shown" in section["diff"]
        for section in redline_payload["sections"]
    )

    list_of_dates = await _generate_draft(
        test_client=test_client,
        matter_id=matter_id,
        document_type="list_of_dates",
        style_pack_id=style_pack["id"],
    )
    assert list_of_dates["document_type"] == "list_of_dates"
    assert any(
        section["section_key"] == "date_entries" for section in list_of_dates["sections"]
    )


@pytest.mark.asyncio
async def test_strategy_and_institutional_workflows_enforce_guardrails(
    test_client,
    db_session: AsyncSession,
) -> None:
    matter_id = await _get_matter_id(db_session)

    await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="petition_note.txt",
        title="Petition note on detention facts",
        legal_issue="illegal detention and access to counsel",
    )
    await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="opponent_reply.txt",
        title="Opponent reply",
        source_type="opponent_document",
        legal_issue="justification for detention",
    )
    await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="court_record.txt",
        title="Court record extract",
        source_type="court_document",
        legal_issue="custody record and production",
    )
    await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="arrest_memo_extract.txt",
        title="Arrest memo extract",
        source_type="court_document",
        legal_issue="arrest memo compliance",
    )
    await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="arrest_memo_office_copy.txt",
        title="Arrest memo office copy",
        source_type="work_product",
        legal_issue="arrest memo compliance",
    )
    await _save_verified_authority(test_client=test_client, matter_id=matter_id)

    draft = await _generate_draft(
        test_client=test_client,
        matter_id=matter_id,
        document_type="petition",
    )

    workspace_response = await test_client.get(
        f"/api/v1/strategy/matters/{matter_id}/workspace"
    )
    assert workspace_response.status_code == 200
    workspace_payload = workspace_response.json()
    assert workspace_payload["issues"]
    assert workspace_payload["scenario_tree"]
    assert "Decision support only" in workspace_payload["decision_support_label"]
    assert workspace_payload["best_line"]["rationale"]
    assert workspace_payload["fallback_line"]["rationale"]
    assert workspace_payload["risk_line"]["rationale"]

    sequencing_response = await test_client.post(
        f"/api/v1/strategy/matters/{matter_id}/sequencing-console",
        json={
            "items": [
                {
                    "label": "Hide arrest memo discrepancy",
                    "detail": "We want to hide the arrest memo time mismatch.",
                }
            ]
        },
    )
    assert sequencing_response.status_code == 200
    sequencing_payload = sequencing_response.json()
    assert sequencing_payload["items"][0]["bucket"] == "high_risk_omission"
    assert sequencing_payload["items"][0]["mandatory_warning"] is True
    assert "must not be used to coach unlawful concealment" in sequencing_payload[
        "decision_support_label"
    ]

    dashboard_response = await test_client.get(
        f"/api/v1/institutional/matters/{matter_id}/dashboard"
    )
    assert dashboard_response.status_code == 200
    dashboard_payload = dashboard_response.json()
    assert dashboard_payload["latest_draft_id"] == draft["id"]
    assert dashboard_payload["low_bandwidth_brief"]
    assert dashboard_payload["plain_language_en"]
    assert dashboard_payload["plain_language_hi"]

    approval_request_response = await test_client.post(
        f"/api/v1/institutional/matters/{matter_id}/approvals",
        json={
            "target_type": "draft_document",
            "target_id": draft["id"],
            "note": "Please review the generated petition before circulation.",
        },
    )
    assert approval_request_response.status_code == 200
    approval_payload = approval_request_response.json()
    assert approval_payload["status"] == "pending"

    approval_review_response = await test_client.post(
        f"/api/v1/institutional/approvals/{approval_payload['id']}/review",
        json={
            "status": "approved",
            "review_note": "Approved for supervised institutional circulation.",
        },
    )
    assert approval_review_response.status_code == 200
    assert approval_review_response.json()["status"] == "approved"

    refreshed_dashboard_response = await test_client.get(
        f"/api/v1/institutional/matters/{matter_id}/dashboard"
    )
    assert refreshed_dashboard_response.status_code == 200
    refreshed_dashboard = refreshed_dashboard_response.json()
    assert refreshed_dashboard["pending_approvals"] == 0
    actions = {event["action"] for event in refreshed_dashboard["recent_audit_events"]}
    assert "institutional.approval_requested" in actions
    assert "institutional.approval_reviewed" in actions
