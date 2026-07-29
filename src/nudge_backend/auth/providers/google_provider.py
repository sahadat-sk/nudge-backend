from typing import Any

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import HTTPException, status
from starlette.requests import Request

from nudge_backend.auth.providers.base import OAuthProvider
from nudge_backend.schemas.auth import GoogleUserInfo


class GoogleProvider(OAuthProvider):
    def __init__(self, oauth: OAuth):
        self._client = oauth.google

    async def authorize_redirect(self, request: Request, redirect_uri: str):
        return await self._client.authorize_redirect(request, redirect_uri)

    async def authorize_access_token(self, request: Request) -> dict[str, Any]:
        try:
            return await self._client.authorize_access_token(request)
        except OAuthError as exc:
            # Covers things like the user denying consent, an expired
            # `state`, or Google rejecting the exchange outright.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google authorization failed: {exc.error}",
            ) from exc

    async def parse_id_token(self, request: Request, token: dict[str, Any]) -> GoogleUserInfo:
        # Authlib >=1.0 already validates the ID token (signature, nonce,
        # issuer, expiry) inside authorize_access_token() and attaches the
        # decoded claims here. Do NOT call self._client.parse_id_token(...)
        # manually — that method's real signature is
        # parse_id_token(self, token, nonce=None, ...), not
        # (request, token). Passing `request` positionally makes Authlib
        # try to read token["id_token"] off the Request object itself,
        # which raises KeyError: 'id_token' (see authlib/authlib#387).
        claims = token.get("userinfo")
        if claims is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google did not return ID token claims; ensure 'openid' scope is requested",
            )

        if not claims.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Google account email is not verified",
            )

        return GoogleUserInfo(
            sub=claims["sub"],
            email=claims["email"],
            email_verified=claims.get("email_verified", False),
            name=claims.get("name"),
            picture=claims.get("picture"),
        )
