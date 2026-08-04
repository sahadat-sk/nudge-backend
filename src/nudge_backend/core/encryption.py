from cryptography.fernet import Fernet, InvalidToken

from nudge_backend.core.config import settings

_fernet = Fernet(settings.token_encryption_key.encode())


def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(value: str) -> str:
    try:
        return _fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        # Almost always means TOKEN_ENCRYPTION_KEY was rotated without a
        # migration plan for existing rows. Surface this loudly rather
        # than silently failing downstream Google API calls.
        raise ValueError(
            "Failed to decrypt stored token; encryption key may have changed") from exc
