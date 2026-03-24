from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import DraftDocumentType, DraftStatus

if TYPE_CHECKING:
    from app.domain.document import Document
    from app.domain.matter import Matter
    from app.domain.organization import Organization
    from app.domain.research import SavedAuthority
    from app.domain.user import User


class StylePack(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "style_packs"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tone: Mapped[str] = mapped_column(String(255), nullable=False)
    opening_phrase: Mapped[str] = mapped_column(String(255), nullable=False)
    prayer_style: Mapped[str] = mapped_column(String(255), nullable=False)
    citation_style: Mapped[str] = mapped_column(String(255), nullable=False)
    voice_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_document_titles: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship()
    created_by: Mapped[User] = relationship()
    draft_documents: Mapped[list[DraftDocument]] = relationship(back_populates="style_pack")


class DraftDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "draft_documents"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[UUID] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    style_pack_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("style_packs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    previous_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("draft_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    document_type: Mapped[DraftDocumentType] = mapped_column(
        Enum(DraftDocumentType),
        nullable=False,
    )
    status: Mapped[DraftStatus] = mapped_column(
        Enum(DraftStatus),
        nullable=False,
        default=DraftStatus.DRAFT,
        server_default=DraftStatus.DRAFT.name,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    export_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    matter: Mapped[Matter] = relationship()
    created_by: Mapped[User] = relationship()
    style_pack: Mapped[StylePack | None] = relationship(back_populates="draft_documents")
    previous_version: Mapped[DraftDocument | None] = relationship(remote_side="DraftDocument.id")
    sections: Mapped[list[DraftSection]] = relationship(
        back_populates="draft_document",
        cascade="all, delete-orphan",
        order_by="DraftSection.order_index.asc()",
    )
    authority_links: Mapped[list[DraftAuthorityLink]] = relationship(
        back_populates="draft_document",
        cascade="all, delete-orphan",
        order_by="DraftAuthorityLink.position_index.asc()",
    )
    annexures: Mapped[list[DraftAnnexure]] = relationship(
        back_populates="draft_document",
        cascade="all, delete-orphan",
        order_by="DraftAnnexure.order_index.asc()",
    )


class DraftSection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "draft_sections"

    draft_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("draft_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_key: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    placeholder_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    draft_document: Mapped[DraftDocument] = relationship(back_populates="sections")


class DraftAuthorityLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "draft_authority_links"

    draft_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("draft_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    saved_authority_id: Mapped[UUID] = mapped_column(
        ForeignKey("saved_authorities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_key: Mapped[str] = mapped_column(String(128), nullable=False)
    position_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    draft_document: Mapped[DraftDocument] = relationship(back_populates="authority_links")
    saved_authority: Mapped[SavedAuthority] = relationship()


class DraftAnnexure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "draft_annexures"

    draft_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("draft_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    draft_document: Mapped[DraftDocument] = relationship(back_populates="annexures")
    source_document: Mapped[Document | None] = relationship()
