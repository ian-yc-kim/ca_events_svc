from __future__ import annotations

import os
from fastapi import FastAPI
from app.routers import events_router


def create_app(env: str | None = None) -> FastAPI:
    """
    Application factory for the events-service.

    Args:
        env: Optional explicit environment name. If None, APP_ENV from environment is used.
             Defaults to "development" when APP_ENV is unset.

    Returns:
        Configured FastAPI application instance.
    """
    env_name = (env or os.getenv("APP_ENV", "development")).lower()
    debug = env_name == "development"

    app = FastAPI(title="events-service", version="0.1.0", debug=debug)

    app.include_router(events_router, prefix="/events", tags=["events"])  # placeholder router

    return app


# ASGI app for uvicorn: `uvicorn app.main:app`
app = create_app()
