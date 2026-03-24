from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.domain.enums import AuthorityKind, DocumentSourceType, MatterStage, MatterStatus, UserRole
from app.domain.matter import Matter
from app.domain.organization import Organization
from app.domain.user import User
from app.services.ingestion import IngestionMetadata, IngestionService


@dataclass(slots=True)
class SeedContext:
    organization: Organization
    user: User
    matter: Matter


class SeedService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.ingestion = IngestionService(session)

    async def seed_demo(self, payload_path: Path | None = None) -> SeedContext:
        payload = json.loads((payload_path or self.settings.seed_data_path).read_text("utf-8"))

        existing = await self.session.execute(
            select(Organization).where(Organization.slug == payload["organization"]["slug"])
        )
        organization = existing.scalar_one_or_none()
        if organization is None:
            organization = Organization(
                name=payload["organization"]["name"],
                slug=payload["organization"]["slug"],
            )
            self.session.add(organization)
            await self.session.flush()

        user = (
            await self.session.execute(select(User).where(User.email == payload["user"]["email"]))
        ).scalar_one_or_none()
        if user is None:
            user = User(
                organization_id=organization.id,
                email=payload["user"]["email"],
                full_name=payload["user"]["full_name"],
                password_hash=hash_password(payload["user"]["password"]),
                role=UserRole.ADMIN,
            )
            self.session.add(user)
            await self.session.flush()

        matter = (
            await self.session.execute(
                select(Matter).where(Matter.reference_code == payload["matter"]["reference_code"])
            )
        ).scalar_one_or_none()
        if matter is None:
            matter = Matter(
                organization_id=organization.id,
                owner_user_id=user.id,
                title=payload["matter"]["title"],
                reference_code=payload["matter"]["reference_code"],
                forum=payload["matter"]["forum"],
                stage=MatterStage(payload["matter"]["stage"]),
                status=MatterStatus.ACTIVE,
                next_hearing_date=date.fromisoformat(payload["matter"]["next_hearing_date"]),
                summary=payload["matter"]["summary"],
            )
            self.session.add(matter)
            await self.session.flush()

        await self.session.commit()

        for document in payload.get("documents", []):
            source_path = Path(document["source_path"])
            file_path = source_path if source_path.is_absolute() else Path.cwd() / source_path
            if not file_path.exists():
                continue
            metadata = IngestionMetadata(
                organization_id=organization.id,
                created_by_user_id=user.id,
                matter_id=matter.id if document["attach_to_matter"] else None,
                source_type=DocumentSourceType(document["source_type"]),
                title=document["title"],
                authority_kind=AuthorityKind(document["authority_kind"]),
                citation_text=document.get("citation_text"),
                court=document.get("court"),
                forum=document.get("forum"),
                bench=document.get("bench"),
                legal_issue=document.get("legal_issue"),
                source_url=document.get("source_url"),
            )
            await self.ingestion.ingest_bytes(
                payload=file_path.read_bytes(),
                file_name=file_path.name,
                content_type=document["content_type"],
                metadata=metadata,
            )

        return SeedContext(organization=organization, user=user, matter=matter)
