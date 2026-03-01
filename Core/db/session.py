# core/db/session.py
from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from core.config.settings import settings

# Engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
    future=True,
)

def get_db():
    """
    FastAPI dependency that yields a DB session and ensures it is closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def db_session():
    """
    Context manager for scripts/CLI usage.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()