from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import TimeStampedModel


class User(TimeStampedModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    resume: Mapped["Resume"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")  # noqa: F821
    search_preferences: Mapped[list["SearchPreference"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    applications: Mapped[list["Application"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821
    memory_entries: Mapped[list["MemoryEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<User {self.email}>"

