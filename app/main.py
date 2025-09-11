from __future__ import annotations

from fastapi import FastAPI
from pydantic import ValidationError

from app.config import get_settings
from app.routers import events_router
from app.db.session import engine, SessionLocal, dispose_engine


def create_app(env: str | None = None) -> FastAPI:
    """
    Application factory for the events-service.

    Args:
        env: Optional explicit environment name (kept for compatibility). Not used for debug.

    Returns:
        Configured FastAPI application instance.
    """
    try:
        settings = get_settings()
    except ValidationError as e:
        import logging
        logging.error(e, exc_info=True)
        raise RuntimeError(f"Invalid configuration: {e}")

    debug = settings.app_env == "development"

    app = FastAPI(title="events-service", version="0.1.0", debug=debug)

    # Attach settings to app state for global access
    app.state.settings = settings

    # Attach DB engine and sessionmaker to app state
    app.state.db_engine = engine
    app.state.session_maker = SessionLocal

    app.include_router(events_router, prefix="/events", tags=["events"])  # placeholder router

    @app.on_event("shutdown")
    def _shutdown_db() -> None:
        try:
            dispose_engine()
        except Exception as e:  # pragma: no cover - defensive
            import logging
            logging.error(e, exc_info=True)

    return app


# ASGI app for uvicorn: `uvicorn app.main:app`
app = create_app()
