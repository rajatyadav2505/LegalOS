from __future__ import annotations

from pathlib import Path

import pytest
from app.domain.enums import DocumentSourceType
from app.domain.matter import Matter
from app.domain.user import User
from app.services.bundle_analysis import BundleAnalysisService
from app.services.ingestion import IngestionMetadata, IngestionService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _get_matter(db_session: AsyncSession) -> Matter:
    return (await db_session.execute(select(Matter).limit(1))).scalar_one()


async def _get_user(db_session: AsyncSession) -> User:
    return (await db_session.execute(select(User).limit(1))).scalar_one()


async def _upload_document(
    *,
    test_client,
    matter_id: str,
    fixture_name: str,
    title: str,
    source_type: str,
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


@pytest.mark.asyncio
async def test_bundle_map_surfaces_phase_two_intelligence(
    test_client,
    db_session: AsyncSession,
) -> None:
    matter = await _get_matter(db_session)
    matter_id = str(matter.id)

    petition = await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="petition_note.txt",
        title="Draft petition note on detention facts",
        source_type="my_document",
        legal_issue="illegal detention and access to counsel",
    )
    assert petition["processing_status"] == "ready"
    assert petition["processing_progress"] == 100

    await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="opponent_reply.txt",
        title="State reply note",
        source_type="opponent_document",
        legal_issue="justification for detention",
    )
    await _upload_document(
        test_client=test_client,
        matter_id=matter_id,
        fixture_name="court_record.txt",
        title="Remand sheet extract",
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

    bundle_response = await test_client.get(f"/api/v1/matters/{matter_id}/bundle")
    assert bundle_response.status_code == 200
    bundle_payload = bundle_response.json()

    assert bundle_payload["matter_reference_code"] == matter.reference_code
    assert bundle_payload["ingestion"]["overall_status"] == "ready"
    assert bundle_payload["ingestion"]["ready_documents"] >= 5

    chronology_dates = {item["date"] for item in bundle_payload["chronology"]}
    assert "2026-03-14" in chronology_dates
    assert "2026-03-15" in chronology_dates

    contradiction_issues = {item["issue"] for item in bundle_payload["contradictions"]}
    assert "Counsel access" in contradiction_issues
    assert "Family notice" in contradiction_issues

    assert bundle_payload["duplicate_groups"]
    assert bundle_payload["duplicate_groups"][0]["duplicate_count"] >= 2

    assert bundle_payload["exhibit_links"]
    exhibit_labels = {item["exhibit_label"] for item in bundle_payload["exhibit_links"]}
    assert "Arrest Memo Extract" in exhibit_labels or "Remand Sheet Extract" in exhibit_labels

    cluster_types = {item["cluster_type"] for item in bundle_payload["clusters"]}
    assert "issue" in cluster_types
    assert "source_type" in cluster_types

    assert len(bundle_payload["documents"]) >= 5
    assert all(item["processing_status"] == "ready" for item in bundle_payload["documents"])


@pytest.mark.asyncio
async def test_queue_upload_surfaces_bundle_processing_counts(
    db_session: AsyncSession,
) -> None:
    matter = await _get_matter(db_session)
    user = await _get_user(db_session)
    ingestion = IngestionService(db_session)

    document = await ingestion.queue_bytes(
        payload=Path("tests/fixtures/sample_matter/petition_note.txt").read_bytes(),
        file_name="petition_note.txt",
        content_type="text/plain",
        metadata=IngestionMetadata(
            organization_id=user.organization_id,
            created_by_user_id=user.id,
            matter_id=matter.id,
            source_type=DocumentSourceType.MY_DOCUMENT,
            title="Queued petition note",
            legal_issue="illegal detention and access to counsel",
        ),
    )
    assert document.processing_status == "queued"

    bundle_payload = await BundleAnalysisService(db_session).get_matter_bundle(
        matter_id=matter.id,
        organization_id=user.organization_id,
    )

    assert bundle_payload.ingestion.overall_status == "queued"
    assert bundle_payload.ingestion.queued_documents == 1
    assert bundle_payload.documents[0].processing_stage == "queued"
    assert bundle_payload.documents[0].processing_progress == 5
