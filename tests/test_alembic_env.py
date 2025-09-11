from __future__ import annotations

import importlib
import os
from types import SimpleNamespace
from typing import Any, Dict

import pytest

from app.db.base import Base


def test_target_metadata_matches_base() -> None:
    # Importing env should not raise when DATABASE_URL is valid
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
    env_module = importlib.import_module("alembic.env")
    assert getattr(env_module, "target_metadata") is Base.metadata


def test_offline_config_uses_settings_url(monkeypatch: pytest.MonkeyPatch) -> None:
    # Set a valid-looking URL
    url = "postgresql://user:pass@localhost:5432/db"
    os.environ["DATABASE_URL"] = url

    configured: Dict[str, Any] = {}

    def fake_configure(**kwargs: Any) -> None:
        configured.update(kwargs)

    class DummyTxn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    # Monkeypatch alembic.context.configure and .begin_transaction used in offline
    import alembic.context as ctx

    monkeypatch.setattr(ctx, "configure", fake_configure)
    monkeypatch.setattr(ctx, "begin_transaction", lambda: DummyTxn())
    monkeypatch.setattr(ctx, "is_offline_mode", lambda: True)

    # Reload env to execute the offline branch
    if "alembic.env" in list(importlib.sys.modules.keys()):
        importlib.invalidate_caches()
        del importlib.sys.modules["alembic.env"]

    importlib.import_module("alembic.env")

    assert configured.get("url") == url
    assert configured.get("target_metadata") is Base.metadata
    assert configured.get("literal_binds") is True


def test_import_raises_with_invalid_database_url(monkeypatch: pytest.MonkeyPatch):
    # Ensure invalid URL causes settings validation to fail during env import
    os.environ["DATABASE_URL"] = "sqlite:///not-allowed.db"  # invalid per Settings

    # Force online/offline decision path; it doesn't matter which branch is chosen
    import alembic.context as ctx
    monkeypatch.setattr(ctx, "is_offline_mode", lambda: True)

    if "alembic.env" in list(importlib.sys.modules.keys()):
        importlib.invalidate_caches()
        del importlib.sys.modules["alembic.env"]

    with pytest.raises(ValueError):
        importlib.import_module("alembic.env")
