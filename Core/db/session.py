# core/db/session.py
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config.settings import settings


def _build_engine():
    database_url = settings.database_url

    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            future=True,
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )


engine = _build_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()