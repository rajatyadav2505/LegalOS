from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache
from importlib import import_module

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        future=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        class_=AsyncSession,
    )


class SessionFactoryProxy:
    def __call__(self, **kwargs: object) -> AsyncSession:
        return get_session_factory()(**kwargs)


SessionLocal = SessionFactoryProxy()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def create_all_tables() -> None:
    for module_name in (
        "app.domain.audit",
        "app.domain.bundle",
        "app.domain.court_intelligence",
        "app.domain.drafting",
        "app.domain.document",
        "app.domain.institutional",
        "app.domain.jobs",
        "app.domain.matter",
        "app.domain.organization",
        "app.domain.research",
        "app.domain.user",
    ):
        import_module(module_name)

    async with get_engine().begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
