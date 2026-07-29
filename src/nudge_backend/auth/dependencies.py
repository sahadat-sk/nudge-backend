from typing import Annotated
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from nudge_backend.core.security import decode_access_token
from nudge_backend.dependencies.database import get_db
from nudge_backend.models.user import User
from nudge_backend.repositories.user_repository import UserRepository

# tokenUrl is only used to populate OpenAPI docs' "Authorize" flow; the
# actual token is issued via /auth/google/callback + /auth/refresh, not a
# password grant.
_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/refresh", auto_error=False)


def get_current_user(
    token: str | None = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise unauthorized

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise unauthorized from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise unauthorized

    try:
        user = UserRepository(db).get_by_id(uuid.UUID(user_id))
    except ValueError as exc:
        raise unauthorized from exc

    if user is None or not user.is_active:
        raise unauthorized

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
