import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class CoverLetter(TimeStampedModel):
    __tablename__ = "cover_letters"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    draft_text: Mapped[str | None] = mapped_column(Text)
    final_text: Mapped[str | None] = mapped_column(Text)
    resume_bullets: Mapped[str | None] = mapped_column(Text)
    revision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critic_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped["Application"] = relationship(back_populates="cover_letter")  # noqa: F821
