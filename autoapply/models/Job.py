from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class Job(TimeStampedModel):
    __tablename__ = "jobs"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    fit_score: Mapped[float | None] = mapped_column(Float)
    recommendation: Mapped[str | None] = mapped_column(String(10))
    fit_reasoning: Mapped[str | None] = mapped_column(Text)

    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunks: Mapped[list["JobChunk"]] = relationship(back_populates="job", cascade="all, delete-orphan")  # noqa: F821
    applications: Mapped[list["Application"]] = relationship(back_populates="job", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Job {self.title} @ {self.company}>"
