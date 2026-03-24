from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.domain.enums import AuthorityTreatment

if TYPE_CHECKING:
    from app.domain.document import Citation, QuoteSpan
    from app.domain.matter import Matter
    from app.domain.user import User


class SavedAuthority(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "saved_authorities"
    __table_args__ = (
        Index(
            "ix_saved_authorities_matter_treatment",
            "matter_id",
            "treatment",
        ),
    )

    matter_id: Mapped[UUID] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("citations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quote_span_id: Mapped[UUID] = mapped_column(
        ForeignKey("quote_spans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    treatment: Mapped[AuthorityTreatment] = mapped_column(
        Enum(AuthorityTreatment),
        nullable=False,
    )
    issue_label: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    matter: Mapped[Matter] = relationship(back_populates="saved_authorities")
    citation: Mapped[Citation | None] = relationship()
    quote_span: Mapped[QuoteSpan] = relationship()
    created_by: Mapped[User] = relationship(back_populates="saved_authorities")
