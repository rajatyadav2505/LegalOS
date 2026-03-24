from __future__ import annotations

import asyncio

from app.db.session import SessionLocal, create_all_tables
from app.services.seed import SeedService


async def _main() -> None:
    await create_all_tables()
    async with SessionLocal() as session:
        await SeedService(session).seed_demo()


if __name__ == "__main__":
    asyncio.run(_main())
