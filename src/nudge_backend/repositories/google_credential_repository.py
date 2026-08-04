import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from nudge_backend.core.encryption import encrypt
from nudge_backend.models.google_credential import GoogleCredential


class GoogleCredentialRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_user_id(self, user_id: uuid.UUID) -> GoogleCredential | None:
        stmt = select(GoogleCredential).where(
            GoogleCredential.user_id == user_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        *,
        user_id: uuid.UUID,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime,
        scope: str,
    ) -> GoogleCredential:
        """
        Create or update this user's stored credential.

        `refresh_token` is None on a re-consent where Google chose not to
        reissue one (it only guarantees a refresh token on the very first
        grant, or when `prompt=consent` forces re-approval — which is why
        the connect flow always passes `prompt=consent`). If we already
        have a row, keep the existing refresh token in that case.
        """
        existing = self.get_by_user_id(user_id)

        if existing is not None:
            existing.access_token_encrypted = encrypt(access_token)
            if refresh_token:
                existing.refresh_token_encrypted = encrypt(refresh_token)
            existing.expires_at = expires_at
            existing.scope = scope
            self._db.flush()
            return existing

        if not refresh_token:
            raise ValueError(
                "Google did not return a refresh token on first connect; "
                "this should not happen with prompt=consent and access_type=offline"
            )

        record = GoogleCredential(
            user_id=user_id,
            access_token_encrypted=encrypt(access_token),
            refresh_token_encrypted=encrypt(refresh_token),
            expires_at=expires_at,
            scope=scope,
        )
        self._db.add(record)
        self._db.flush()
        return record

    def delete(self, record: GoogleCredential) -> None:
        self._db.delete(record)
        self._db.flush()
