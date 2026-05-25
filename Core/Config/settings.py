# core/config/settings.py
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "Phishing Simulation Prototype"
    environment: str = "development"
    secret_key: str = Field(..., alias="SECRET_KEY")

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Redis / Celery
    redis_url: str = Field(..., alias="REDIS_URL")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # Tracker / outbox
    tracker_base_url: str = Field(default="http://127.0.0.1:8001", alias="TRACKER_BASE_URL")
    outbox_dir: str = Field(default="data/outbox", alias="OUTBOX_DIR")

    # SMTP
    smtp_host: str = Field(default="smtp.example.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="demo", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="demo", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    # JWT
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")


settings = Settings()