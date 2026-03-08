# core/config/settings.py
from __future__ import annotations

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = Field(..., env="SECRET_KEY")
    database_url: str = Field(..., env="DATABASE_URL")

    smtp_host: str = Field(..., env="SMTP_HOST")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: str = Field(..., env="SMTP_USERNAME")
    smtp_password: str = Field(..., env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")

    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")

    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")

    tracker_base_url: str = Field("http://127.0.0.1:8001", env="TRACKER_BASE_URL")
    outbox_dir: str = Field("data/outbox", env="OUTBOX_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()