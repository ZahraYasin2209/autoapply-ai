import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class ApplicationOutcome(TimeStampedModel):
    __tablename__ = "application_outcomes"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    application: Mapped["Application"] = relationship(back_populates="outcome")  # noqa: F821
