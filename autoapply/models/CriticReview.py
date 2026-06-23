import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class CriticReview(TimeStampedModel):
    __tablename__ = "critic_reviews"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False
    )

    verdict: Mapped[str] = mapped_column(String(10), nullable=False)
    feedback_text: Mapped[str | None] = mapped_column(Text)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    application: Mapped["Application"] = relationship(back_populates="critic_reviews")  # noqa: F821
