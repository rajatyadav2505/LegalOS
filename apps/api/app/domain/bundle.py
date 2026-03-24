from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import EntityType, RelationSeverity, RelationType

if TYPE_CHECKING:
    from app.domain.document import Document, QuoteSpan
    from app.domain.matter import Matter


class ChronologyEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chronology_events"
    __table_args__ = (
        Index("ix_chronology_events_matter_date", "matter_id", "event_date"),
    )

    matter_id: Mapped[UUID] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quote_span_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quote_spans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    actor_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        server_default="0.5",
    )

    matter: Mapped[Matter] = relationship()
    document: Mapped[Document] = relationship()
    quote_span: Mapped[QuoteSpan | None] = relationship()


class DocumentEntity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_entities"
    __table_args__ = (
        Index("ix_document_entities_matter_normalized", "matter_id", "normalized_label"),
        Index("ix_document_entities_document_type", "document_id", "entity_type"),
    )

    matter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quote_span_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quote_spans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(255), nullable=False)
    paragraph_start: Mapped[int] = mapped_column(nullable=False)
    paragraph_end: Mapped[int] = mapped_column(nullable=False)
    page_start: Mapped[int | None] = mapped_column(nullable=True)
    page_end: Mapped[int | None] = mapped_column(nullable=True)

    matter: Mapped[Matter | None] = relationship()
    document: Mapped[Document] = relationship()
    quote_span: Mapped[QuoteSpan | None] = relationship()


class ExhibitReference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "exhibit_references"
    __table_args__ = (
        Index("ix_exhibit_references_matter_normalized", "matter_id", "normalized_label"),
    )

    matter_id: Mapped[UUID] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quote_span_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quote_spans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(255), nullable=False)
    context_text: Mapped[str] = mapped_column(Text, nullable=False)

    matter: Mapped[Matter] = relationship()
    document: Mapped[Document] = relationship()
    quote_span: Mapped[QuoteSpan | None] = relationship()


class DocumentRelation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_relations"
    __table_args__ = (
        Index("ix_document_relations_matter_type", "matter_id", "relation_type"),
        Index("ix_document_relations_left_right", "left_document_id", "right_document_id"),
    )

    matter_id: Mapped[UUID] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type: Mapped[RelationType] = mapped_column(Enum(RelationType), nullable=False)
    severity: Mapped[RelationSeverity | None] = mapped_column(
        Enum(RelationSeverity),
        nullable=True,
    )
    left_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    right_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    left_quote_span_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quote_spans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    right_quote_span_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quote_spans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        server_default="0.5",
    )

    matter: Mapped[Matter] = relationship()
    left_document: Mapped[Document] = relationship(foreign_keys=[left_document_id])
    right_document: Mapped[Document] = relationship(foreign_keys=[right_document_id])
    left_quote_span: Mapped[QuoteSpan | None] = relationship(foreign_keys=[left_quote_span_id])
    right_quote_span: Mapped[QuoteSpan | None] = relationship(foreign_keys=[right_quote_span_id])
