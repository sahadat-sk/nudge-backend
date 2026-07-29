import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from nudge_backend.core.security import IssuedRefreshToken
from nudge_backend.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self._db = db

    def create(self, *, user_id: uuid.UUID, issued: IssuedRefreshToken, expires_at: datetime) -> RefreshToken:
        record = RefreshToken(
            user_id=user_id,
            selector=issued.selector,
            verifier_hash=issued.verifier_hash,
            expires_at=expires_at,
        )
        self._db.add(record)
        self._db.flush()
        return record

    def get_by_selector(self, selector: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.selector == selector)
        return self._db.execute(stmt).scalar_one_or_none()

    def revoke(self, record: RefreshToken) -> None:
        record.revoked_at = datetime.now(timezone.utc)
        self._db.flush()

    def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Used for reuse-detection: kill every session for this user."""
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        for record in self._db.execute(stmt).scalars():
            record.revoked_at = datetime.now(timezone.utc)
        self._db.flush()

    def mark_replaced(self, old: RefreshToken, new: RefreshToken) -> None:
        old.replaced_by_id = new.id
        self._db.flush()
