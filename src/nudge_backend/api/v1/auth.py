from fastapi import Cookie
from fastapi import HTTPException
from nudge_backend.models.user import User
from nudge_backend.schemas.auth import SessionResponse, UserResponse
from nudge_backend.auth.dependencies import get_current_user
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from nudge_backend.auth.google import oauth
from nudge_backend.auth.providers.google_provider import GoogleProvider
from nudge_backend.core.config import settings
from nudge_backend.dependencies.database import get_db
from nudge_backend.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

provider = GoogleProvider(oauth)


@router.get("/google/login")
async def google_login(
    request: Request,
):
    return await provider.authorize_redirect(
        request,
        settings.google_redirect_uri,
    )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    token = await provider.authorize_access_token(
        request,
    )

    google_user = await provider.parse_id_token(
        request,
        token,
    )

    service = AuthService(db)

    login = service.login_google(
        google_user=google_user,
        google_token=token,
    )

    response = RedirectResponse(
        url=f"{settings.frontend_url}",
        status_code=302,
    )

    response.set_cookie(
        key="refresh_token",
        value=login.refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )

    return response


@router.post("/refresh")
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token is None:
        raise HTTPException(
            status_code=401,
            detail="Missing refresh token",
        )

    service = AuthService(db)

    tokens = service.refresh(
        refresh_token,
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )

    return {
        "access_token": tokens.access_token,
        "token_type": "Bearer",
    }


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        AuthService(db).logout(refresh_token)

    response.delete_cookie(
        key="refresh_token",
        path="/",
    )

    return {
        "message": "Logged out",
    }


@router.get("/me", response_model=SessionResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return SessionResponse(user=UserResponse.model_validate(current_user))
