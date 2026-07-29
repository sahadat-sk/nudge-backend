from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nudge_backend.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from nudge_backend.models.refresh_token import RefreshToken


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(
        String(1024), nullable=True)

    # Google's stable, unique subject identifier ("sub" claim). Distinct from
    # our own primary key so we can add other providers later without
    # colliding identifier spaces.
    google_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
