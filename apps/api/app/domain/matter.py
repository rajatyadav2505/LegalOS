from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import MatterStage, MatterStatus

if TYPE_CHECKING:
    from app.domain.document import Document
    from app.domain.organization import Organization
    from app.domain.research import SavedAuthority
    from app.domain.user import User


class Matter(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "matters"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    forum: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[MatterStage] = mapped_column(Enum(MatterStage), nullable=False)
    status: Mapped[MatterStatus] = mapped_column(
        Enum(MatterStatus),
        nullable=False,
        default=MatterStatus.ACTIVE,
    )
    next_hearing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="matters")
    owner: Mapped[User] = relationship(back_populates="matters")
    documents: Mapped[list[Document]] = relationship(back_populates="matter")
    saved_authorities: Mapped[list[SavedAuthority]] = relationship(back_populates="matter")
