from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import AuthorityKind, DocumentSourceType, ProcessingStatus

if TYPE_CHECKING:
    from app.domain.matter import Matter
    from app.domain.organization import Organization


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_org_matter_source", "organization_id", "matter_id", "source_type"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[DocumentSourceType] = mapped_column(
        Enum(DocumentSourceType),
        nullable=False,
        default=DocumentSourceType.MY_DOCUMENT,
        server_default=DocumentSourceType.MY_DOCUMENT.name,
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus),
        nullable=False,
        default=ProcessingStatus.QUEUED,
        server_default=ProcessingStatus.QUEUED.name,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    extraction_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    authority_kind: Mapped[AuthorityKind] = mapped_column(
        Enum(AuthorityKind),
        nullable=False,
        default=AuthorityKind.MATTER_DOCUMENT,
        server_default=AuthorityKind.MATTER_DOCUMENT.name,
    )
    citation_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    court: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bench: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    legal_issue: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="documents")
    matter: Mapped[Matter | None] = relationship(back_populates="documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document")
    citations: Mapped[list[Citation]] = relationship(back_populates="document")
    quote_spans: Mapped[list[QuoteSpan]] = relationship(back_populates="document")


class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        Index(
            "ix_document_chunks_document_paragraph",
            "document_id",
            "paragraph_start",
            "paragraph_end",
        ),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading: Mapped[str | None] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    paragraph_start: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph_end: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped[Document] = relationship(back_populates="chunks")


class Citation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "citations"

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citation_text: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    authority_kind: Mapped[AuthorityKind] = mapped_column(Enum(AuthorityKind), nullable=False)
    court: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bench: Mapped[str | None] = mapped_column(String(255), nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    legal_issue: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    document: Mapped[Document] = relationship(back_populates="citations")
    quote_spans: Mapped[list[QuoteSpan]] = relationship(back_populates="citation")


class QuoteSpan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quote_spans"
    __table_args__ = (
        Index(
            "ix_quote_spans_document_paragraph",
            "document_id",
            "paragraph_start",
            "paragraph_end",
        ),
        Index("ix_quote_spans_checksum", "checksum"),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("citations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    anchor_label: Mapped[str] = mapped_column(String(255), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    paragraph_start: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph_end: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped[Document] = relationship(back_populates="quote_spans")
    citation: Mapped[Citation | None] = relationship(back_populates="quote_spans")
