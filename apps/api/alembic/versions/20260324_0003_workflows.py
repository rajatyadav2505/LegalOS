"""drafting strategy institutional workflows

Revision ID: 20260324_0003
Revises: 20260324_0002
Create Date: 2026-03-24 22:35:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260324_0003"
down_revision = "20260324_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    draft_document_type = sa.Enum(
        "PETITION",
        "REPLY",
        "WRITTEN_SUBMISSION",
        "AFFIDAVIT",
        "APPLICATION",
        "SYNOPSIS",
        "LIST_OF_DATES",
        "LEGAL_NOTICE",
        "SETTLEMENT_NOTE",
        name="draftdocumenttype",
    )
    draft_status = sa.Enum("DRAFT", "REVIEW", "EXPORTED", name="draftstatus")
    approval_status = sa.Enum("PENDING", "APPROVED", "REJECTED", name="approvalstatus")
    approval_target_type = sa.Enum(
        "DRAFT_DOCUMENT",
        "STRATEGY_WORKSPACE",
        name="approvaltargettype",
    )

    bind = op.get_bind()
    for enum_type in (
        draft_document_type,
        draft_status,
        approval_status,
        approval_target_type,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "style_packs",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tone", sa.String(length=255), nullable=False),
        sa.Column("opening_phrase", sa.String(length=255), nullable=False),
        sa.Column("prayer_style", sa.String(length=255), nullable=False),
        sa.Column("citation_style", sa.String(length=255), nullable=False),
        sa.Column("voice_notes", sa.Text(), nullable=True),
        sa.Column("sample_document_titles", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_style_packs_created_by_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_style_packs_organization_id_organizations"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_style_packs")),
    )
    op.create_index(op.f("ix_style_packs_created_by_user_id"), "style_packs", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_style_packs_organization_id"), "style_packs", ["organization_id"], unique=False)

    op.create_table(
        "draft_documents",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("matter_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("style_pack_id", sa.Uuid(), nullable=True),
        sa.Column("previous_version_id", sa.Uuid(), nullable=True),
        sa.Column("document_type", draft_document_type, nullable=False),
        sa.Column("status", draft_status, server_default="DRAFT", nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("export_file_name", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_draft_documents_created_by_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_draft_documents_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_draft_documents_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["previous_version_id"], ["draft_documents.id"], name=op.f("fk_draft_documents_previous_version_id_draft_documents"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["style_pack_id"], ["style_packs.id"], name=op.f("fk_draft_documents_style_pack_id_style_packs"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_draft_documents")),
    )
    op.create_index(op.f("ix_draft_documents_created_by_user_id"), "draft_documents", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_draft_documents_matter_id"), "draft_documents", ["matter_id"], unique=False)
    op.create_index(op.f("ix_draft_documents_organization_id"), "draft_documents", ["organization_id"], unique=False)
    op.create_index(op.f("ix_draft_documents_previous_version_id"), "draft_documents", ["previous_version_id"], unique=False)
    op.create_index(op.f("ix_draft_documents_style_pack_id"), "draft_documents", ["style_pack_id"], unique=False)

    op.create_table(
        "draft_sections",
        sa.Column("draft_document_id", sa.Uuid(), nullable=False),
        sa.Column("section_key", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("placeholder_count", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["draft_document_id"], ["draft_documents.id"], name=op.f("fk_draft_sections_draft_document_id_draft_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_draft_sections")),
    )
    op.create_index(op.f("ix_draft_sections_draft_document_id"), "draft_sections", ["draft_document_id"], unique=False)

    op.create_table(
        "draft_authority_links",
        sa.Column("draft_document_id", sa.Uuid(), nullable=False),
        sa.Column("saved_authority_id", sa.Uuid(), nullable=False),
        sa.Column("section_key", sa.String(length=128), nullable=False),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["draft_document_id"], ["draft_documents.id"], name=op.f("fk_draft_authority_links_draft_document_id_draft_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["saved_authority_id"], ["saved_authorities.id"], name=op.f("fk_draft_authority_links_saved_authority_id_saved_authorities"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_draft_authority_links")),
    )
    op.create_index(op.f("ix_draft_authority_links_draft_document_id"), "draft_authority_links", ["draft_document_id"], unique=False)
    op.create_index(op.f("ix_draft_authority_links_saved_authority_id"), "draft_authority_links", ["saved_authority_id"], unique=False)

    op.create_table(
        "draft_annexures",
        sa.Column("draft_document_id", sa.Uuid(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), nullable=True),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["draft_document_id"], ["draft_documents.id"], name=op.f("fk_draft_annexures_draft_document_id_draft_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], name=op.f("fk_draft_annexures_source_document_id_documents"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_draft_annexures")),
    )
    op.create_index(op.f("ix_draft_annexures_draft_document_id"), "draft_annexures", ["draft_document_id"], unique=False)
    op.create_index(op.f("ix_draft_annexures_source_document_id"), "draft_annexures", ["source_document_id"], unique=False)

    op.create_table(
        "approval_requests",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("matter_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("target_type", approval_target_type, nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("status", approval_status, server_default="PENDING", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], name=op.f("fk_approval_requests_matter_id_matters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name=op.f("fk_approval_requests_organization_id_organizations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], name=op.f("fk_approval_requests_requested_by_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], name=op.f("fk_approval_requests_reviewed_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approval_requests")),
    )
    op.create_index(op.f("ix_approval_requests_matter_id"), "approval_requests", ["matter_id"], unique=False)
    op.create_index(op.f("ix_approval_requests_organization_id"), "approval_requests", ["organization_id"], unique=False)
    op.create_index(op.f("ix_approval_requests_requested_by_user_id"), "approval_requests", ["requested_by_user_id"], unique=False)
    op.create_index(op.f("ix_approval_requests_reviewed_by_user_id"), "approval_requests", ["reviewed_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_approval_requests_reviewed_by_user_id"), table_name="approval_requests")
    op.drop_index(op.f("ix_approval_requests_requested_by_user_id"), table_name="approval_requests")
    op.drop_index(op.f("ix_approval_requests_organization_id"), table_name="approval_requests")
    op.drop_index(op.f("ix_approval_requests_matter_id"), table_name="approval_requests")
    op.drop_table("approval_requests")

    op.drop_index(op.f("ix_draft_annexures_source_document_id"), table_name="draft_annexures")
    op.drop_index(op.f("ix_draft_annexures_draft_document_id"), table_name="draft_annexures")
    op.drop_table("draft_annexures")

    op.drop_index(op.f("ix_draft_authority_links_saved_authority_id"), table_name="draft_authority_links")
    op.drop_index(op.f("ix_draft_authority_links_draft_document_id"), table_name="draft_authority_links")
    op.drop_table("draft_authority_links")

    op.drop_index(op.f("ix_draft_sections_draft_document_id"), table_name="draft_sections")
    op.drop_table("draft_sections")

    op.drop_index(op.f("ix_draft_documents_style_pack_id"), table_name="draft_documents")
    op.drop_index(op.f("ix_draft_documents_previous_version_id"), table_name="draft_documents")
    op.drop_index(op.f("ix_draft_documents_organization_id"), table_name="draft_documents")
    op.drop_index(op.f("ix_draft_documents_matter_id"), table_name="draft_documents")
    op.drop_index(op.f("ix_draft_documents_created_by_user_id"), table_name="draft_documents")
    op.drop_table("draft_documents")

    op.drop_index(op.f("ix_style_packs_organization_id"), table_name="style_packs")
    op.drop_index(op.f("ix_style_packs_created_by_user_id"), table_name="style_packs")
    op.drop_table("style_packs")

    bind = op.get_bind()
    for enum_name in (
        "approvaltargettype",
        "approvalstatus",
        "draftstatus",
        "draftdocumenttype",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
