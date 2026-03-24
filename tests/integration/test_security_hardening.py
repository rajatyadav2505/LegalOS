from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from app.core.config import get_settings
from app.core.security import hash_password
from app.domain.document import QuoteSpan
from app.domain.enums import (
    AuthorityKind,
    AuthorityTreatment,
    DocumentSourceType,
    MatterStage,
    MatterStatus,
    UserRole,
)
from app.domain.matter import Matter
from app.domain.organization import Organization
from app.domain.research import SavedAuthority
from app.domain.user import User
from app.services.ingestion import IngestionMetadata, IngestionService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _first_matter_id(db_session: AsyncSession) -> str:
    matter = (await db_session.execute(select(Matter).limit(1))).scalar_one()
    return str(matter.id)


async def _create_foreign_matter_data(
    db_session: AsyncSession,
) -> tuple[Matter, QuoteSpan]:
    organization = Organization(name="Foreign Org", slug=f"foreign-{uuid4().hex[:8]}")
    db_session.add(organization)
    await db_session.flush()

    user = User(
        organization_id=organization.id,
        email=f"foreign-{uuid4().hex[:8]}@legalos.local",
        full_name="Foreign User",
        password_hash=hash_password("DemoPass123!"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()

    matter = Matter(
        organization_id=organization.id,
        owner_user_id=user.id,
        title="Foreign Matter",
        reference_code=f"FOR-{uuid4().hex[:6]}",
        forum="Delhi High Court",
        stage=MatterStage.NOTICE,
        status=MatterStatus.ACTIVE,
        summary="Foreign matter used for tenant-isolation tests.",
    )
    db_session.add(matter)
    await db_session.flush()

    document = await IngestionService(db_session).ingest_bytes(
        payload=Path("tests/fixtures/sample_matter/petition_note.txt").read_bytes(),
        file_name="petition_note.txt",
        content_type="text/plain",
        metadata=IngestionMetadata(
            organization_id=organization.id,
            created_by_user_id=user.id,
            matter_id=matter.id,
            source_type=DocumentSourceType.MY_DOCUMENT,
            title="Foreign petition note",
            authority_kind=AuthorityKind.MATTER_DOCUMENT,
            legal_issue="foreign detention note",
        ),
    )
    quote_span = (
        await db_session.execute(
            select(QuoteSpan).where(QuoteSpan.document_id == document.id).limit(1)
        )
    ).scalar_one()
    db_session.add(
        SavedAuthority(
            matter_id=matter.id,
            quote_span_id=quote_span.id,
            citation_id=None,
            created_by_user_id=user.id,
            treatment=AuthorityTreatment.APPLY,
            issue_label="Foreign issue",
            note="Tenant isolation test",
        )
    )
    await db_session.commit()
    return matter, quote_span


@pytest.mark.asyncio
async def test_research_routes_enforce_organization_scoping(
    test_client,
    db_session: AsyncSession,
) -> None:
    first_matter_id = await _first_matter_id(db_session)
    foreign_matter, foreign_quote_span = await _create_foreign_matter_data(db_session)

    save_response = await test_client.post(
        f"/api/v1/research/matters/{first_matter_id}/saved-authorities",
        json={
            "quote_span_id": str(foreign_quote_span.id),
            "citation_id": None,
            "treatment": "apply",
            "issue_label": "Cross-org quote span",
            "note": "This should fail",
        },
    )
    assert save_response.status_code == 404

    quote_lock_response = await test_client.get(
        f"/api/v1/research/quote-spans/{foreign_quote_span.id}"
    )
    assert quote_lock_response.status_code == 404

    export_response = await test_client.get(
        f"/api/v1/research/matters/{foreign_matter.id}/export"
    )
    assert export_response.status_code == 404


@pytest.mark.asyncio
async def test_upload_rejects_files_over_configured_limit(
    test_client,
    db_session: AsyncSession,
) -> None:
    matter_id = await _first_matter_id(db_session)
    settings = get_settings()
    original_limit = settings.max_upload_size_bytes
    settings.max_upload_size_bytes = 128
    try:
        response = await test_client.post(
            "/api/v1/documents/upload",
            data={
                "matter_id": matter_id,
                "source_type": "my_document",
                "title": "Too large file",
                "authority_kind": "matter_document",
                "process_in_background": "false",
            },
            files={
                "file": (
                    "too-big.txt",
                    b"x" * 256,
                    "text/plain",
                )
            },
        )
    finally:
        settings.max_upload_size_bytes = original_limit

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_login_rate_limit_blocks_repeated_failures(test_client) -> None:
    email = f"blocked-{uuid4().hex[:8]}@example.com"
    payload = {"email": email, "password": "wrong-password"}

    for _ in range(5):
        response = await test_client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401

    blocked_response = await test_client.post("/api/v1/auth/login", json=payload)
    assert blocked_response.status_code == 429
