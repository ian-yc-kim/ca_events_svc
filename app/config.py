from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings loaded from environment variables and .env file."""

    app_env: Literal["development", "production", "test"] = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str
    pagination_default_limit: int = 50
    pagination_max_limit: int = 200

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("app_env", mode="before")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        if v is None:
            return "development"
        value = str(v).strip().lower()
        allowed = {"development", "production", "test"}
        if value not in allowed:
            raise ValueError("APP_ENV must be one of development, production, test")
        return value

    @field_validator("host", mode="before")
    @classmethod
    def validate_host(cls, v: str) -> str:
        value = str(v).strip()
        if not value:
            raise ValueError("HOST must be a non-empty string")
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= int(v) <= 65535):
            raise ValueError("PORT must be between 1 and 65535")
        return int(v)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        value = str(v)
        if not value.startswith("postgresql://"):
            raise ValueError('DATABASE_URL must start with "postgresql://"')
        return value

    @field_validator("pagination_default_limit")
    @classmethod
    def validate_pagination_default_limit(cls, v: int) -> int:
        if int(v) <= 0:
            raise ValueError("PAGINATION_DEFAULT_LIMIT must be > 0")
        return int(v)

    @model_validator(mode="after")
    def validate_pagination_limits(self) -> "Settings":
        if self.pagination_max_limit < self.pagination_default_limit:
            raise ValueError(
                "PAGINATION_MAX_LIMIT must be >= PAGINATION_DEFAULT_LIMIT"
            )
        return self


# Internal cached builder
@lru_cache(maxsize=1)
def _build_settings() -> Settings:
    return Settings()


_ENV_FINGERPRINT: tuple[str | None, ...] | None = None


def _current_env_fingerprint() -> tuple[str | None, ...]:
    # Only include relevant variables that affect Settings
    return (
        os.getenv("APP_ENV"),
        os.getenv("HOST"),
        os.getenv("PORT"),
        os.getenv("DATABASE_URL"),
        os.getenv("PAGINATION_DEFAULT_LIMIT"),
        os.getenv("PAGINATION_MAX_LIMIT"),
    )


def get_settings() -> Settings:
    """Return cached settings instance loaded from environment/.env.

    If relevant environment variables change between calls (e.g., across tests),
    invalidate the cache to reflect the new environment.
    """
    global _ENV_FINGERPRINT
    fp = _current_env_fingerprint()
    if fp != _ENV_FINGERPRINT:
        _build_settings.cache_clear()
        _ENV_FINGERPRINT = fp
    return _build_settings()
