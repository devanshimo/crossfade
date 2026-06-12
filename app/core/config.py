"""
app/core/config.py
──────────────────
Central configuration object backed by Pydantic Settings.

Why it exists:
    All environment-derived configuration lives here.  Every other module
    imports `get_settings()` so the validated config is available app-wide
    without scattering os.environ calls.

How it connects:
    • Imported by db/session.py  → DATABASE_URL
    • Imported by services/spotify.py → Spotify credentials
    • Imported by core/security.py  → SECRET_KEY
    • Imported by main.py           → APP_ENV / LOG_LEVEL
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    secret_key: str
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str  # kept as str so we can mutate the scheme below

    # ── Spotify ───────────────────────────────────────────────────────────────
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str

    # Spotify OAuth constants – not env-driven, kept here for single-source clarity
    spotify_auth_url: str = "https://accounts.spotify.com/authorize"
    spotify_token_url: str = "https://accounts.spotify.com/api/token"
    spotify_api_base: str = "https://api.spotify.com/v1"
    spotify_scopes: str = "user-read-private user-read-email playlist-read-private playlist-read-collaborative"

    @field_validator("database_url")
    @classmethod
    def ensure_asyncpg_scheme(cls, v: str) -> str:
        """
        Guard against accidentally supplying a sync psycopg2 URL.
        SQLAlchemy 2.0 async requires the +asyncpg dialect.
        """
        if v.startswith("postgresql://") or v.startswith("postgres://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("secret_key")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.

    Using lru_cache means the .env file is parsed exactly once for the
    lifetime of the process, which is the correct behaviour for a long-running
    API server.  Tests that need to override settings can call
    `get_settings.cache_clear()` and monkeypatch env vars before re-calling.
    """
    return Settings()  # type: ignore[call-arg]
