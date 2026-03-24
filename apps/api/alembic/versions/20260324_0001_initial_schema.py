"""initial schema

Revision ID: 20260324_0001
Revises:
Create Date: 2026-03-24 15:10:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260324_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = sa.Enum("ADMIN", "MEMBER", name="userrole")
    matter_status = sa.Enum("ACTIVE", "HOLD", "CLOSED", name="matterstatus")
    matter_stage = sa.Enum(
        "PRE_FILING",
        "FILING",
        "NOTICE",
        "EVIDENCE",
        "ARGUMENTS",
        "ORDERS",
        name="matterstage",
    )
    source_type = sa.Enum(
        "PUBLIC_LAW",
        "MY_DOCUMENT",
        "OPPONENT_DOCUMENT",
        "COURT_DOCUMENT",
        "WORK_PRODUCT",
        name="documentsourcetype",
    )
    processing_status = sa.Enum(
        "QUEUED",
        "PROCESSING",
        "READY",
        "FAILED",
        name="processingstatus",
    )
    authority_kind = sa.Enum(
        "CONSTITUTION",
        "STATUTE",
        "JUDGMENT",
        "NOTE",
        "MATTER_DOCUMENT",
        name="authoritykind",
    )
    authority_treatment = sa.Enum(
        "APPLY",
        "DISTINGUISH",
        "ADVERSE",
        "DRAFT",
        name="authoritytreatment",
    )

    bind = op.get_bind()
    for enum_type in (
        user_role,
        matter_status,
        matter_stage,
        source_type,
        processing_status,
        authority_kind,
        authority_treatment,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "organizations",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("slug", name=op.f("uq_organizations_slug")),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_users_organization_id_organizations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_organization_id"), "users", ["organization_id"], unique=False)

    op.create_table(
        "matters",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("reference_code", sa.String(length=64), nullable=False),
        sa.Column("forum", sa.String(length=255), nullable=False),
        sa.Column("stage", matter_stage, nullable=False),
        sa.Column("status", matter_status, nullable=False),
        sa.Column("next_hearing_date", sa.Date(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_matters_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name=op.f("fk_matters_owner_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matters")),
        sa.UniqueConstraint("reference_code", name=op.f("uq_matters_reference_code")),
    )
    op.create_index(op.f("ix_matters_organization_id"), "matters", ["organization_id"], unique=False)
    op.create_index(op.f("ix_matters_owner_user_id"), "matters", ["owner_user_id"], unique=False)
    op.create_index(op.f("ix_matters_reference_code"), "matters", ["reference_code"], unique=True)

    op.create_table(
        "documents",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("matter_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", source_type, server_default="MY_DOCUMENT", nullable=False),
        sa.Column("processing_status", processing_status, server_default="QUEUED", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column(
            "authority_kind",
            authority_kind,
            server_default="MATTER_DOCUMENT",
            nullable=False,
        ),
        sa.Column("citation_text", sa.String(length=255), nullable=True),
        sa.Column("court", sa.String(length=255), nullable=True),
        sa.Column("forum", sa.String(length=255), nullable=True),
        sa.Column("bench", sa.String(length=255), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("legal_issue", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_documents_created_by_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_documents_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_documents_organization_id_organizations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index(op.f("ix_documents_created_by_user_id"), "documents", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_documents_legal_issue"), "documents", ["legal_issue"], unique=False)
    op.create_index(op.f("ix_documents_matter_id"), "documents", ["matter_id"], unique=False)
    op.create_index(op.f("ix_documents_organization_id"), "documents", ["organization_id"], unique=False)
    op.create_index(op.f("ix_documents_sha256"), "documents", ["sha256"], unique=False)
    op.create_index("ix_documents_org_matter_source", "documents", ["organization_id", "matter_id", "source_type"], unique=False)

    op.create_table(
        "citations",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("citation_text", sa.String(length=255), nullable=False),
        sa.Column("authority_kind", authority_kind, nullable=False),
        sa.Column("court", sa.String(length=255), nullable=True),
        sa.Column("forum", sa.String(length=255), nullable=True),
        sa.Column("bench", sa.String(length=255), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("legal_issue", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_citations_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_citations")),
    )
    op.create_index(op.f("ix_citations_citation_text"), "citations", ["citation_text"], unique=False)
    op.create_index(op.f("ix_citations_document_id"), "citations", ["document_id"], unique=False)
    op.create_index(op.f("ix_citations_legal_issue"), "citations", ["legal_issue"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("paragraph_start", sa.Integer(), nullable=False),
        sa.Column("paragraph_end", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_document_chunks_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
    )
    op.create_index(op.f("ix_document_chunks_document_id"), "document_chunks", ["document_id"], unique=False)
    op.create_index("ix_document_chunks_document_paragraph", "document_chunks", ["document_id", "paragraph_start", "paragraph_end"], unique=False)

    op.create_table(
        "quote_spans",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("citation_id", sa.Uuid(), nullable=True),
        sa.Column("anchor_label", sa.String(length=255), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("paragraph_start", sa.Integer(), nullable=False),
        sa.Column("paragraph_end", sa.Integer(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], name=op.f("fk_quote_spans_citation_id_citations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_quote_spans_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quote_spans")),
    )
    op.create_index(op.f("ix_quote_spans_citation_id"), "quote_spans", ["citation_id"], unique=False)
    op.create_index(op.f("ix_quote_spans_document_id"), "quote_spans", ["document_id"], unique=False)
    op.create_index("ix_quote_spans_checksum", "quote_spans", ["checksum"], unique=False)
    op.create_index("ix_quote_spans_document_paragraph", "quote_spans", ["document_id", "paragraph_start", "paragraph_end"], unique=False)

    op.create_table(
        "saved_authorities",
        sa.Column("matter_id", sa.Uuid(), nullable=False),
        sa.Column("citation_id", sa.Uuid(), nullable=True),
        sa.Column("quote_span_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("treatment", authority_treatment, nullable=False),
        sa.Column("issue_label", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["citation_id"], ["citations.id"], name=op.f("fk_saved_authorities_citation_id_citations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_saved_authorities_created_by_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_saved_authorities_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_span_id"], ["quote_spans.id"], name=op.f("fk_saved_authorities_quote_span_id_quote_spans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_saved_authorities")),
    )
    op.create_index(op.f("ix_saved_authorities_citation_id"), "saved_authorities", ["citation_id"], unique=False)
    op.create_index(op.f("ix_saved_authorities_created_by_user_id"), "saved_authorities", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_saved_authorities_matter_id"), "saved_authorities", ["matter_id"], unique=False)
    op.create_index(op.f("ix_saved_authorities_quote_span_id"), "saved_authorities", ["quote_span_id"], unique=False)
    op.create_index("ix_saved_authorities_matter_treatment", "saved_authorities", ["matter_id", "treatment"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_events_actor_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_audit_events_organization_id_organizations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(op.f("ix_audit_events_action"), "audit_events", ["action"], unique=False)
    op.create_index(op.f("ix_audit_events_actor_user_id"), "audit_events", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_events_organization_id"), "audit_events", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_organization_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_actor_user_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_action"), table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_saved_authorities_matter_treatment", table_name="saved_authorities")
    op.drop_index(op.f("ix_saved_authorities_quote_span_id"), table_name="saved_authorities")
    op.drop_index(op.f("ix_saved_authorities_matter_id"), table_name="saved_authorities")
    op.drop_index(op.f("ix_saved_authorities_created_by_user_id"), table_name="saved_authorities")
    op.drop_index(op.f("ix_saved_authorities_citation_id"), table_name="saved_authorities")
    op.drop_table("saved_authorities")

    op.drop_index("ix_quote_spans_document_paragraph", table_name="quote_spans")
    op.drop_index("ix_quote_spans_checksum", table_name="quote_spans")
    op.drop_index(op.f("ix_quote_spans_document_id"), table_name="quote_spans")
    op.drop_index(op.f("ix_quote_spans_citation_id"), table_name="quote_spans")
    op.drop_table("quote_spans")

    op.drop_index("ix_document_chunks_document_paragraph", table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_id"), table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index(op.f("ix_citations_legal_issue"), table_name="citations")
    op.drop_index(op.f("ix_citations_document_id"), table_name="citations")
    op.drop_index(op.f("ix_citations_citation_text"), table_name="citations")
    op.drop_table("citations")

    op.drop_index("ix_documents_org_matter_source", table_name="documents")
    op.drop_index(op.f("ix_documents_sha256"), table_name="documents")
    op.drop_index(op.f("ix_documents_organization_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_matter_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_legal_issue"), table_name="documents")
    op.drop_index(op.f("ix_documents_created_by_user_id"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(op.f("ix_matters_reference_code"), table_name="matters")
    op.drop_index(op.f("ix_matters_owner_user_id"), table_name="matters")
    op.drop_index(op.f("ix_matters_organization_id"), table_name="matters")
    op.drop_table("matters")

    op.drop_index(op.f("ix_users_organization_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")

    bind = op.get_bind()
    for enum_name in (
        "authoritytreatment",
        "authoritykind",
        "processingstatus",
        "documentsourcetype",
        "matterstage",
        "matterstatus",
        "userrole",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
