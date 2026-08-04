from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Values are read from environment variables (or a `.env` file in local
    development). Never hardcode secrets — this class only declares the
    shape and defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- General ---
    # "development" | "staging" | "production"
    environment: str = Field(default="development")
    frontend_url: str = Field(default="http://localhost:3000")

    # --- Database ---
    database_url: str

    # --- Google OAuth (login) ---
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # --- Google Calendar (separate, incremental consent) ---
    google_calendar_redirect_uri: str
    # Symmetric key for encrypting stored Google Calendar tokens at rest.
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    token_encryption_key: str

    # --- Sessions (Starlette SessionMiddleware, used to carry short-lived
    # state across OAuth redirects, e.g. which user initiated calendar
    # connect) ---
    session_secret_key: str

    # --- JWT / Sessions ---
    jwt_secret_key: str
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=30)
    session_secret: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    # lru_cache means the .env / environment is only parsed once per process.
    return Settings()


settings = get_settings()
