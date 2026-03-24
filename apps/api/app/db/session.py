from __future__ import annotations

from collections.abc import AsyncGenerator
from importlib import import_module

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def create_all_tables() -> None:
    for module_name in (
        "app.domain.audit",
        "app.domain.bundle",
        "app.domain.drafting",
        "app.domain.document",
        "app.domain.institutional",
        "app.domain.matter",
        "app.domain.organization",
        "app.domain.research",
        "app.domain.user",
    ):
        import_module(module_name)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
