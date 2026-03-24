from __future__ import annotations

from pathlib import Path

import pytest
from app.domain.document import QuoteSpan
from app.domain.enums import AuthorityKind, DocumentSourceType
from app.domain.matter import Matter
from app.domain.user import User
from app.services.ingestion import IngestionMetadata, IngestionService
from app.services.quote_lock import QuoteLockService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_quote_lock_validates_stored_span_checksums(db_session: AsyncSession) -> None:
    matter = (await db_session.execute(select(Matter).limit(1))).scalar_one()
    user = (await db_session.execute(select(User).limit(1))).scalar_one()

    service = IngestionService(db_session)
    payload = Path("tests/fixtures/sample_matter/petition_note.txt").read_bytes()
    await service.ingest_bytes(
        payload=payload,
        file_name="petition_note.txt",
        content_type="text/plain",
        metadata=IngestionMetadata(
            organization_id=user.organization_id,
            created_by_user_id=user.id,
            matter_id=matter.id,
            source_type=DocumentSourceType.MY_DOCUMENT,
            authority_kind=AuthorityKind.MATTER_DOCUMENT,
            title="Draft petition note on detention facts",
            legal_issue="illegal detention and access to counsel",
        ),
    )

    quote_spans = (await db_session.execute(select(QuoteSpan))).scalars().all()
    assert quote_spans
    first_span = quote_spans[0]
    assert QuoteLockService.matches(first_span.text, first_span.checksum) is True
    assert QuoteLockService.matches(first_span.text + " modified", first_span.checksum) is False
