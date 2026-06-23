import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class Resume(TimeStampedModel):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    file_path: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="resume")  # noqa: F821
    chunks: Mapped[list["ResumeChunk"]] = relationship(back_populates="resume", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Resume user_id={self.user_id}>"
