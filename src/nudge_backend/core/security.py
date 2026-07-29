import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from nudge_backend.core.config import settings

ACCESS_TOKEN_TYPE = "access"


# --------------------------------------------------------------------------
# Access tokens (short-lived JWTs, never persisted server-side)
# --------------------------------------------------------------------------

def create_access_token(*, subject: str, extra_claims: dict | None = None) -> str:
    """Issue a short-lived JWT identifying `subject` (the user id)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises jwt.PyJWTError (or subclasses) on any invalid/expired/tampered
    token — callers should catch this and translate it into a 401.
    """
    payload = jwt.decode(token, settings.jwt_secret_key,
                         algorithms=[settings.jwt_algorithm])
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


# --------------------------------------------------------------------------
# Refresh tokens
#
# We never store raw refresh tokens in the database (same principle as
# passwords). Instead each token is:
#
#   raw_token = "<selector>.<verifier>"
#
#   - selector: random, stored PLAINTEXT and indexed, so we can look the row
#     up in O(1) without scanning/hashing every stored token.
#   - verifier: random, stored only as a SHA-256 hash. Even if the DB leaks,
#     the attacker cannot reconstruct usable tokens.
#
# This is the same "split token" pattern used by Laravel Sanctum / Django
# REST Framework's token auth for anything that can't use bcrypt-style
# lookups (bcrypt hashes can't be searched by prefix, so a fixed selector
# is what makes the DB lookup possible at all).
# --------------------------------------------------------------------------

_SELECTOR_BYTES = 9   # -> 12 url-safe chars
_VERIFIER_BYTES = 32  # -> 43 url-safe chars


@dataclass(frozen=True)
class IssuedRefreshToken:
    raw_token: str       # give this to the client (goes in the cookie)
    selector: str        # store in DB, plaintext, unique-indexed
    verifier_hash: str   # store in DB, sha256 hex digest


def generate_refresh_token() -> IssuedRefreshToken:
    selector = secrets.token_urlsafe(_SELECTOR_BYTES)
    verifier = secrets.token_urlsafe(_VERIFIER_BYTES)
    verifier_hash = _hash_verifier(verifier)
    return IssuedRefreshToken(
        raw_token=f"{selector}.{verifier}",
        selector=selector,
        verifier_hash=verifier_hash,
    )


def split_refresh_token(raw_token: str) -> tuple[str, str]:
    """Split a raw cookie value into (selector, verifier). Raises ValueError if malformed."""
    try:
        selector, verifier = raw_token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Malformed refresh token") from exc
    if not selector or not verifier:
        raise ValueError("Malformed refresh token")
    return selector, verifier


def verify_refresh_token(raw_token: str, expected_verifier_hash: str) -> bool:
    """Constant-time comparison of a presented token against the stored hash."""
    try:
        _, verifier = split_refresh_token(raw_token)
    except ValueError:
        return False
    return hmac.compare_digest(_hash_verifier(verifier), expected_verifier_hash)


def _hash_verifier(verifier: str) -> str:
    return hashlib.sha256(verifier.encode("utf-8")).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
