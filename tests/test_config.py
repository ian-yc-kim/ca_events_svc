import re
import importlib
import pytest


VALID_DB = 'postgresql://user:pass@localhost:5432/testdb'


def test_missing_database_url_fails_startup(monkeypatch):
    # Load module under a valid environment first to avoid import-time failure
    monkeypatch.setenv('DATABASE_URL', VALID_DB)
    from app import main as main_module

    # Now remove DATABASE_URL and APP_ENV to simulate missing configuration
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('APP_ENV', raising=False)

    with pytest.raises(RuntimeError) as exc:
        main_module.create_app()
    msg = str(exc.value)
    assert 'Invalid configuration' in msg
    assert 'DATABASE_URL' in msg


def test_settings_validation_rules(monkeypatch):
    from app import main as main_module

    # Start with a base valid env
    monkeypatch.setenv('DATABASE_URL', VALID_DB)
    importlib.reload(main_module)

    # Invalid PORT
    monkeypatch.setenv('PORT', '70000')
    with pytest.raises(RuntimeError) as exc1:
        main_module.create_app()
    assert 'PORT' in str(exc1.value)

    # Reset invalid PORT, test invalid DATABASE_URL
    monkeypatch.delenv('PORT', raising=False)
    monkeypatch.setenv('DATABASE_URL', 'mysql://user:pass@localhost:3306/testdb')
    with pytest.raises(RuntimeError) as exc2:
        main_module.create_app()
    assert 'DATABASE_URL' in str(exc2.value)

    # Reset to valid DB, test invalid PAGINATION_DEFAULT_LIMIT
    monkeypatch.setenv('DATABASE_URL', VALID_DB)
    monkeypatch.setenv('PAGINATION_DEFAULT_LIMIT', '0')
    with pytest.raises(RuntimeError) as exc3:
        main_module.create_app()
    assert 'PAGINATION_DEFAULT_LIMIT' in str(exc3.value)

    # Reset default limit and test cross-field: max < default
    monkeypatch.setenv('PAGINATION_DEFAULT_LIMIT', '50')
    monkeypatch.setenv('PAGINATION_MAX_LIMIT', '10')
    with pytest.raises(RuntimeError) as exc4:
        main_module.create_app()
    assert 'PAGINATION_MAX_LIMIT' in str(exc4.value)



def test_settings_attached_to_app_state_and_debug_toggle(monkeypatch):
    from app import main as main_module

    # Production env
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('DATABASE_URL', VALID_DB)
    importlib.reload(main_module)
    app = main_module.create_app()
    assert app.debug is False
    assert hasattr(app.state, 'settings')
    assert app.state.settings.database_url.startswith('postgresql://')

    # Development env
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.setenv('DATABASE_URL', VALID_DB)
    importlib.reload(main_module)
    app2 = main_module.create_app()
    assert app2.debug is True
