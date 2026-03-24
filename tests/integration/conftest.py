from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

os.environ["AUTO_CREATE_DB"] = "false"

import pytest_asyncio
from app.api.deps import get_current_user, get_db_session
from app.core.security import hash_password
from app.db.base import Base
from app.domain.enums import AuthorityKind, DocumentSourceType, MatterStage, MatterStatus, UserRole
from app.domain.matter import Matter
from app.domain.organization import Organization
from app.domain.user import User
from app.main import build_application
from app.services.ingestion import IngestionMetadata, IngestionService
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest_asyncio.fixture
async def db_session(tmp_path: Path) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/legalos-test.db")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        organization = Organization(name="Test Org", slug="test-org")
        session.add(organization)
        await session.flush()

        user = User(
            organization_id=organization.id,
            email="demo@legalos.local",
            full_name="Aditi Rao",
            password_hash=hash_password("DemoPass123!"),
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.flush()

        matter = Matter(
            organization_id=organization.id,
            owner_user_id=user.id,
            title="Seema Kumari v. State",
            reference_code="DL-LEGALOS-TEST",
            forum="Delhi High Court",
            stage=MatterStage.NOTICE,
            status=MatterStatus.ACTIVE,
            summary="Test matter for upload and research flows.",
        )
        session.add(matter)
        await session.commit()

        # Seed public-law corpus alongside matter documents.
        ingestion = IngestionService(session)
        fixture_dir = Path.cwd() / "tests/fixtures/sample_matter/public_law"
        public_docs = [
            (
                fixture_dir / "constitution_article_21.txt",
                "Constitution of India, art. 21",
                "personal liberty and due process",
            ),
            (
                fixture_dir / "constitution_article_22.txt",
                "Constitution of India, art. 22(1)-(2)",
                "arrest safeguards and legal representation",
            ),
            (
                fixture_dir / "constitution_article_39a.txt",
                "Constitution of India, art. 39A",
                "equal justice and free legal aid",
            ),
        ]
        for file_path, citation_text, legal_issue in public_docs:
            await ingestion.ingest_bytes(
                payload=file_path.read_bytes(),
                file_name=file_path.name,
                content_type="text/plain",
                metadata=IngestionMetadata(
                    organization_id=organization.id,
                    created_by_user_id=user.id,
                    source_type=DocumentSourceType.PUBLIC_LAW,
                    title=file_path.stem.replace("_", " ").title(),
                    authority_kind=AuthorityKind.CONSTITUTION,
                    citation_text=citation_text,
                    court="Constitution of India",
                    forum="India",
                    legal_issue=legal_issue,
                    source_url="https://www.legislative.gov.in/static/uploads/2025/08/7af1daa22d65f9d04c00ae9b9aa5a799.pdf",
                ),
            )

        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_user(db_session: AsyncSession) -> User:
    return (await db_session.execute(select(User).limit(1))).scalar_one()


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession, seeded_user: User) -> AsyncIterator[AsyncClient]:
    app = build_application()

    async def override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_current_user() -> User:
        return seeded_user

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
