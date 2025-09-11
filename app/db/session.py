from __future__ import annotations

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def create_engine_from_url(url: str):
    """Create SQLAlchemy engine without establishing a connection eagerly.

    pool_pre_ping ensures stale connections are detected when checked out.
    """
    return create_engine(url, pool_pre_ping=True)


# Lazily create engine using validated settings at import time (no connection made)
_settings = get_settings()
engine = create_engine_from_url(_settings.database_url)

# Session factory; does not connect until a real operation is performed
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy Session.

    - Yields a session for the request scope
    - On exception: rollback and re-raise
    - Always closes the session
    """
    session: Session = SessionLocal()
    try:
        yield session
    except Exception as e:  # pragma: no cover - error path is tested via rollback call
        logging.error(e, exc_info=True)
        try:
            session.rollback()
        except Exception as rollback_err:
            logging.error(rollback_err, exc_info=True)
        raise
    finally:
        try:
            session.close()
        except Exception as close_err:
            logging.error(close_err, exc_info=True)


def get_engine():
    return engine


def get_session_maker():
    return SessionLocal


def dispose_engine() -> None:
    """Dispose the engine's connection pool safely."""
    try:
        engine.dispose()
    except Exception as e:
        logging.error(e, exc_info=True)
