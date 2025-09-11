import importlib
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session


TEST_DB_URL = "postgresql://user:pass@localhost:5432/testdb"


def test_app_state_has_engine_and_session_maker(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    from app import main as main_module
    importlib.reload(main_module)
    app = main_module.create_app()

    assert hasattr(app.state, "db_engine")
    assert hasattr(app.state, "session_maker")

    # Ensure session_maker can produce a Session instance without connecting
    session = app.state.session_maker()
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_get_db_dependency_yields_and_closes(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    from app.db import session as db_session_module
    importlib.reload(db_session_module)

    # Use real SessionLocal to ensure generator yields a real Session
    gen = db_session_module.get_db()
    session = next(gen)
    assert isinstance(session, Session)

    # Closing the generator should close the session without raising
    gen.close()


def test_get_db_dependency_rollback_on_exception(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    # Reload to ensure environment is applied
    import app.db.session as db_session_module
    importlib.reload(db_session_module)

    # Create a fake session to capture rollback/close calls
    flags = SimpleNamespace(rolled_back=False, closed=False)

    class FakeSession:
        def rollback(self):
            flags.rolled_back = True
        def close(self):
            flags.closed = True

    # Monkeypatch SessionLocal to return our FakeSession
    db_session_module.SessionLocal = lambda: FakeSession()

    gen = db_session_module.get_db()
    # Prime the generator to get the session
    _ = next(gen)

    # Throw an exception into the generator to trigger rollback path
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("boom"))

    assert flags.rolled_back is True
    assert flags.closed is True


def test_shutdown_disposes_engine(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    from app import main as main_module
    importlib.reload(main_module)
    app = main_module.create_app()

    # Simulate application shutdown by invoking registered handlers
    for handler in app.router.on_shutdown:
        handler()

    # Also ensure direct dispose does not raise
    from app.db.session import dispose_engine as _dispose
    _dispose()
