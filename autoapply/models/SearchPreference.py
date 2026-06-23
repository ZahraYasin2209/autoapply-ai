import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class SearchPreference(TimeStampedModel):
    __tablename__ = "search_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    target_role: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    seniority_level: Mapped[str | None] = mapped_column(String(50))
    excluded_companies: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User"] = relationship(back_populates="search_preferences")  # noqa: F821

    def __repr__(self) -> str:
        return f"<SearchPreference user_id={self.user_id} role={self.target_role}>"

