"""bundle intelligence

Revision ID: 20260324_0002
Revises: 20260324_0001
Create Date: 2026-03-24 16:05:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260324_0002"
down_revision = "20260324_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    entity_type = sa.Enum(
        "PERSON",
        "ORGANIZATION",
        "ROLE",
        "EXHIBIT",
        "ISSUE",
        name="entitytype",
    )
    relation_type = sa.Enum(
        "CONTRADICTION",
        "DUPLICATE",
        name="relationtype",
    )
    relation_severity = sa.Enum("LOW", "MEDIUM", "HIGH", name="relationseverity")

    bind = op.get_bind()
    for enum_type in (entity_type, relation_type, relation_severity):
        enum_type.create(bind, checkfirst=True)

    op.add_column("documents", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("documents", sa.Column("extraction_method", sa.String(length=64), nullable=True))

    op.create_table(
        "chronology_events",
        sa.Column("matter_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("quote_span_id", sa.Uuid(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("actor_label", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_chronology_events_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_chronology_events_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_span_id"], ["quote_spans.id"], name=op.f("fk_chronology_events_quote_span_id_quote_spans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chronology_events")),
    )
    op.create_index(op.f("ix_chronology_events_document_id"), "chronology_events", ["document_id"], unique=False)
    op.create_index(op.f("ix_chronology_events_matter_id"), "chronology_events", ["matter_id"], unique=False)
    op.create_index(op.f("ix_chronology_events_quote_span_id"), "chronology_events", ["quote_span_id"], unique=False)
    op.create_index("ix_chronology_events_matter_date", "chronology_events", ["matter_id", "event_date"], unique=False)

    op.create_table(
        "document_entities",
        sa.Column("matter_id", sa.Uuid(), nullable=True),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("quote_span_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", entity_type, nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("normalized_label", sa.String(length=255), nullable=False),
        sa.Column("paragraph_start", sa.Integer(), nullable=False),
        sa.Column("paragraph_end", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_document_entities_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_document_entities_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_span_id"], ["quote_spans.id"], name=op.f("fk_document_entities_quote_span_id_quote_spans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_entities")),
    )
    op.create_index(op.f("ix_document_entities_document_id"), "document_entities", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_entities_matter_id"), "document_entities", ["matter_id"], unique=False)
    op.create_index(op.f("ix_document_entities_quote_span_id"), "document_entities", ["quote_span_id"], unique=False)
    op.create_index("ix_document_entities_document_type", "document_entities", ["document_id", "entity_type"], unique=False)
    op.create_index("ix_document_entities_matter_normalized", "document_entities", ["matter_id", "normalized_label"], unique=False)

    op.create_table(
        "exhibit_references",
        sa.Column("matter_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("quote_span_id", sa.Uuid(), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("normalized_label", sa.String(length=255), nullable=False),
        sa.Column("context_text", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_exhibit_references_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_exhibit_references_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_span_id"], ["quote_spans.id"], name=op.f("fk_exhibit_references_quote_span_id_quote_spans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exhibit_references")),
    )
    op.create_index(op.f("ix_exhibit_references_document_id"), "exhibit_references", ["document_id"], unique=False)
    op.create_index(op.f("ix_exhibit_references_matter_id"), "exhibit_references", ["matter_id"], unique=False)
    op.create_index(op.f("ix_exhibit_references_quote_span_id"), "exhibit_references", ["quote_span_id"], unique=False)
    op.create_index("ix_exhibit_references_matter_normalized", "exhibit_references", ["matter_id", "normalized_label"], unique=False)

    op.create_table(
        "document_relations",
        sa.Column("matter_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", relation_type, nullable=False),
        sa.Column("severity", relation_severity, nullable=True),
        sa.Column("left_document_id", sa.Uuid(), nullable=False),
        sa.Column("right_document_id", sa.Uuid(), nullable=False),
        sa.Column("left_quote_span_id", sa.Uuid(), nullable=True),
        sa.Column("right_quote_span_id", sa.Uuid(), nullable=True),
        sa.Column("fingerprint", sa.String(length=128), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["left_document_id"], ["documents.id"], name=op.f("fk_document_relations_left_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["left_quote_span_id"], ["quote_spans.id"], name=op.f("fk_document_relations_left_quote_span_id_quote_spans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_document_relations_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["right_document_id"], ["documents.id"], name=op.f("fk_document_relations_right_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["right_quote_span_id"], ["quote_spans.id"], name=op.f("fk_document_relations_right_quote_span_id_quote_spans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_relations")),
    )
    op.create_index(op.f("ix_document_relations_fingerprint"), "document_relations", ["fingerprint"], unique=False)
    op.create_index(op.f("ix_document_relations_left_document_id"), "document_relations", ["left_document_id"], unique=False)
    op.create_index(op.f("ix_document_relations_left_quote_span_id"), "document_relations", ["left_quote_span_id"], unique=False)
    op.create_index(op.f("ix_document_relations_matter_id"), "document_relations", ["matter_id"], unique=False)
    op.create_index(op.f("ix_document_relations_right_document_id"), "document_relations", ["right_document_id"], unique=False)
    op.create_index(op.f("ix_document_relations_right_quote_span_id"), "document_relations", ["right_quote_span_id"], unique=False)
    op.create_index("ix_document_relations_left_right", "document_relations", ["left_document_id", "right_document_id"], unique=False)
    op.create_index("ix_document_relations_matter_type", "document_relations", ["matter_id", "relation_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_document_relations_matter_type", table_name="document_relations")
    op.drop_index("ix_document_relations_left_right", table_name="document_relations")
    op.drop_index(op.f("ix_document_relations_right_quote_span_id"), table_name="document_relations")
    op.drop_index(op.f("ix_document_relations_right_document_id"), table_name="document_relations")
    op.drop_index(op.f("ix_document_relations_matter_id"), table_name="document_relations")
    op.drop_index(op.f("ix_document_relations_left_quote_span_id"), table_name="document_relations")
    op.drop_index(op.f("ix_document_relations_left_document_id"), table_name="document_relations")
    op.drop_index(op.f("ix_document_relations_fingerprint"), table_name="document_relations")
    op.drop_table("document_relations")

    op.drop_index("ix_exhibit_references_matter_normalized", table_name="exhibit_references")
    op.drop_index(op.f("ix_exhibit_references_quote_span_id"), table_name="exhibit_references")
    op.drop_index(op.f("ix_exhibit_references_matter_id"), table_name="exhibit_references")
    op.drop_index(op.f("ix_exhibit_references_document_id"), table_name="exhibit_references")
    op.drop_table("exhibit_references")

    op.drop_index("ix_document_entities_matter_normalized", table_name="document_entities")
    op.drop_index("ix_document_entities_document_type", table_name="document_entities")
    op.drop_index(op.f("ix_document_entities_quote_span_id"), table_name="document_entities")
    op.drop_index(op.f("ix_document_entities_matter_id"), table_name="document_entities")
    op.drop_index(op.f("ix_document_entities_document_id"), table_name="document_entities")
    op.drop_table("document_entities")

    op.drop_index("ix_chronology_events_matter_date", table_name="chronology_events")
    op.drop_index(op.f("ix_chronology_events_quote_span_id"), table_name="chronology_events")
    op.drop_index(op.f("ix_chronology_events_matter_id"), table_name="chronology_events")
    op.drop_index(op.f("ix_chronology_events_document_id"), table_name="chronology_events")
    op.drop_table("chronology_events")

    op.drop_column("documents", "extraction_method")
    op.drop_column("documents", "processing_completed_at")
    op.drop_column("documents", "processing_started_at")
    op.drop_column("documents", "processing_error")

    bind = op.get_bind()
    for enum_name in ("relationseverity", "relationtype", "entitytype"):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
