import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class Feedback(TimeStampedModel):
    __tablename__ = "feedback"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False
    )

    rating: Mapped[str] = mapped_column(String(10), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    application: Mapped["Application"] = relationship(back_populates="feedback")  # noqa: F821
