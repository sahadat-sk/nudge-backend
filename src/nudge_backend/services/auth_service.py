from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from nudge_backend.core.security import (
    create_access_token,
    generate_refresh_token,
    refresh_token_expiry,
    split_refresh_token,
    verify_refresh_token,
)
from nudge_backend.models.user import User
from nudge_backend.repositories.refresh_token_repository import RefreshTokenRepository
from nudge_backend.repositories.user_repository import UserRepository
from nudge_backend.schemas.auth import GoogleUserInfo, LoginResult, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self._db = db
        self._users = UserRepository(db)
        self._refresh_tokens = RefreshTokenRepository(db)

    # ----------------------------------------------------------------
    # Google login
    # ----------------------------------------------------------------
    def login_google(self, *, google_user: GoogleUserInfo, google_token: dict[str, Any]) -> LoginResult:
        # google_token is accepted for callers that want to persist
        # provider tokens (e.g. to call Google APIs later). We don't need
        # it here, but keeping it in the signature keeps the router simple
        # and leaves room to store it without changing the call site.
        user = self._users.get_or_create_from_google(google_user)

        access_token, refresh_token = self._issue_tokens(user)
        self._db.commit()

        return LoginResult(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user),
        )

    # ----------------------------------------------------------------
    # Refresh (rotates the refresh token on every use)
    # ----------------------------------------------------------------
    def refresh(self, raw_refresh_token: str) -> LoginResult:
        try:
            selector, _ = split_refresh_token(raw_refresh_token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid refresh token") from exc

        record = self._refresh_tokens.get_by_selector(selector)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if record.is_revoked:
            # This selector was already used once (or explicitly revoked).
            # Presenting it again means the token was likely stolen and
            # both the attacker and legitimate user are racing to use it —
            # so we burn every active session for this user and force a
            # fresh login everywhere.
            self._refresh_tokens.revoke_all_for_user(record.user_id)
            self._db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token reuse detected; all sessions revoked",
            )

        if record.is_expired or not verify_refresh_token(raw_refresh_token, record.verifier_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer active")

        access_token, new_raw_refresh_token, new_record = self._rotate(
            record, user)
        self._db.commit()

        return LoginResult(
            access_token=access_token,
            refresh_token=new_raw_refresh_token,
            user=UserResponse.model_validate(user),
        )

    # ----------------------------------------------------------------
    # Logout
    # ----------------------------------------------------------------
    def logout(self, raw_refresh_token: str) -> None:
        try:
            selector, _ = split_refresh_token(raw_refresh_token)
        except ValueError:
            return  # malformed cookie, nothing to revoke

        record = self._refresh_tokens.get_by_selector(selector)
        if record is not None and not record.is_revoked:
            self._refresh_tokens.revoke(record)
            self._db.commit()

    # ----------------------------------------------------------------
    # Internals
    # ----------------------------------------------------------------
    def _issue_tokens(self, user: User) -> tuple[str, str]:
        access_token = create_access_token(subject=str(user.id))
        issued = generate_refresh_token()
        self._refresh_tokens.create(
            user_id=user.id,
            issued=issued,
            expires_at=refresh_token_expiry(),
        )
        return access_token, issued.raw_token

    def _rotate(self, old_record, user: User) -> tuple[str, str, Any]:
        access_token = create_access_token(subject=str(user.id))
        issued = generate_refresh_token()
        new_record = self._refresh_tokens.create(
            user_id=user.id,
            issued=issued,
            expires_at=refresh_token_expiry(),
        )
        self._refresh_tokens.mark_replaced(old_record, new_record)
        self._refresh_tokens.revoke(old_record)
        return access_token, issued.raw_token, new_record
