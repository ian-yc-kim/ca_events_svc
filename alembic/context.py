from __future__ import annotations

# Minimal alembic.context shim to support tests that import and monkeypatch
# alembic.context.* during offline configuration. This is not a full-featured
# Alembic runtime, but provides the interfaces used in tests and in env.py.
from typing import Any, Dict, Optional, Iterator
from contextlib import contextmanager
import os


class _Config:
    def __init__(self) -> None:
        # If an alembic.ini exists in the project root, expose its path
        cfg_file = "alembic.ini"
        self.config_file_name: Optional[str] = cfg_file if os.path.exists(cfg_file) else None
        self.config_ini_section: str = "alembic"

    def get_section(self, name: str) -> Dict[str, Any]:
        # Return an empty section by default; env.py will populate sqlalchemy.url
        return {}


# Expose a module-level Config instance similar to alembic.context.config
config = _Config()

# Storage for last configure kwargs to aid debugging/tests if needed
_last_configure_kwargs: Dict[str, Any] | None = None


def configure(**kwargs: Any) -> None:
    global _last_configure_kwargs
    _last_configure_kwargs = dict(kwargs)


@contextmanager
def begin_transaction() -> Iterator[None]:
    # No-op transaction context manager suitable for offline tests
    yield


def run_migrations() -> None:
    # No-op placeholder; tests only validate that env.py can call this
    # without raising when running in offline mode.
    return None


# Default to offline mode (True) to avoid making real DB connections during
# module import in tests. Individual tests can monkeypatch this as needed.
# This ensures importing alembic.env does not attempt to connect to a database
# unless explicitly requested.

def is_offline_mode() -> bool:  # pragma: no cover - behavior verified via tests
    return True
