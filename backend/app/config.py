"""StegaShield backend configuration.

Loads settings from environment variables or .env file with production-ready defaults.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings backed by pydantic-settings."""

    DATABASE_URL: str = "sqlite:///./stegashield.db"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    FILE_TTL_MINUTES: int = 30
    MAX_UPLOAD_MB: int = 10
    MAX_PIXELS: int = 16_000_000
    STORAGE_DIR: str = "data/files"
    SECRET_KEY: str = "stegashield-dev-secret-key-change-in-production"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_storage_dir(self) -> Path:
        """Resolve and ensure storage directory exists."""
        p = Path(self.STORAGE_DIR)
        if not p.is_absolute():
            p = Path.cwd() / p
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()


settings = get_settings()
