"""Application configuration using Pydantic BaseSettings.

This module defines a Settings class which loads environment variables from
the operating system or a `.env` file if present. It centralizes all
configuration for the project so that other modules can import a single
instance of `settings` and access values like the database URL,
SMTP credentials or Celery broker configuration.

Using Pydantic ensures that types are validated at startup and that
defaults are applied if certain values are not provided. It also supports
loading from a `.env` file located in the project root when using
`python-dotenv`.

Example usage::

    from core.config.settings import settings
    print(settings.database_url)

The values in `.env.example` illustrate which variables should be set.
"""

from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Project-wide configuration loaded from the environment."""

    # Secret key used for signing JWTs and other sensitive operations
    secret_key: str = Field(..., env="SECRET_KEY")

    # Database connection string in SQLAlchemy URL format
    database_url: str = Field(..., env="DATABASE_URL")

    # SMTP configuration for sending emails
    smtp_host: str = Field(..., env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: str = Field(..., env="SMTP_USERNAME")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")

    # Celery broker URL (default uses Redis)
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    # API server configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached access to the Settings instance.

    Using `lru_cache` ensures that the environment is read only once
    during the application's lifetime.
    """
    return Settings()


settings: Settings = get_settings()