import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class GoogleUserInfo(BaseModel):
    """Claims we care about from Google's decoded ID token."""

    sub: str
    email: EmailStr
    email_verified: bool = False
    name: str | None = None
    picture: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    name: str | None
    picture_url: str | None


class SessionResponse(BaseModel):
    """Returned by whoever exposes 'who am I' (e.g. GET /auth/me)."""

    user: UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class LoginResult(BaseModel):
    """Internal result of a successful login/refresh — never returned directly."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    access_token: str
    refresh_token: str
    user: UserResponse
