from abc import ABC, abstractmethod
from typing import Any

from starlette.requests import Request

from nudge_backend.schemas.auth import GoogleUserInfo


class OAuthProvider(ABC):
    """
    Interface every social-login provider must implement.

    Keeping this abstract (rather than calling authlib directly from the
    router) means adding a second provider — e.g. GitHub, Microsoft — later
    only requires a new class, not router changes.
    """

    @abstractmethod
    async def authorize_redirect(self, request: Request, redirect_uri: str):
        """Redirect the browser to the provider's consent screen."""

    @abstractmethod
    async def authorize_access_token(self, request: Request) -> dict[str, Any]:
        """Exchange the callback's `code` for tokens."""

    @abstractmethod
    async def parse_id_token(self, request: Request, token: dict[str, Any]) -> GoogleUserInfo:
        """Validate the ID token and extract the normalized user profile."""
