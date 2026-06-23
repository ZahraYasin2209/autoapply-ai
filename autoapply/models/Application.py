import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class Application(TimeStampedModel):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_job"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped["User"] = relationship(back_populates="applications")  # noqa: F821
    job: Mapped["Job"] = relationship(back_populates="applications")  # noqa: F821
    cover_letter: Mapped["CoverLetter"] = relationship(back_populates="application", uselist=False, cascade="all, delete-orphan")  # noqa: F821
    critic_reviews: Mapped[list["CriticReview"]] = relationship(back_populates="application", cascade="all, delete-orphan")  # noqa: F821
    outcome: Mapped["ApplicationOutcome"] = relationship(back_populates="application", uselist=False, cascade="all, delete-orphan")  # noqa: F821
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="application", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Application user={self.user_id} job={self.job_id} status={self.status}>"
