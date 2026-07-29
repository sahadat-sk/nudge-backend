from typing import TYPE_CHECKING
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nudge_backend.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from nudge_backend.models.user import User


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    # See core/security.py for the selector/verifier scheme.
    selector: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False)
    verifier_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

    # Links rotated tokens into a chain so a reused/stolen token can be
    # detected: if a revoked token is presented again, we revoke the whole
    # chain (see AuthService.refresh).
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_valid(self) -> bool:
        return not self.is_expired and not self.is_revoked
