from authlib.integrations.starlette_client import OAuth

from nudge_backend.core.config import settings

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        # openid is required for parse_id_token(); email/profile give us
        # the fields GoogleUserInfo needs without extra API calls.
        "scope": "openid email profile",
    },
)
