import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nudge_backend.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GoogleCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A user's Google Calendar OAuth grant.

    Deliberately separate from the login-time Google identity (User.google_id):
    a user can be logged in via Google without ever having connected their
    calendar, and revoking calendar access shouldn't touch their session.
    """

    __tablename__ = "google_credentials"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,  # one calendar credential per user
        nullable=False,
        index=True,
    )
    user: Mapped["User"] = relationship()

    # Encrypted at rest — see core/encryption.py. Never log or serialize
    # these fields.
    access_token_encrypted: Mapped[str] = mapped_column(
        String(2048), nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(
        String(2048), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(1024), nullable=False, default="")
