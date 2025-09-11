from fastapi.testclient import TestClient
import importlib

TEST_DB_URL = 'postgresql://user:pass@localhost:5432/testdb'


def test_docs_served(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', TEST_DB_URL)
    from app import main as main_module
    importlib.reload(main_module)
    local_app = main_module.create_app()
    with TestClient(local_app) as client:
        resp = client.get("/docs")
        assert resp.status_code == 200
        text = resp.text
        assert ("Swagger UI" in text) or ("swagger-ui" in text.lower())


def test_openapi_json_served(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', TEST_DB_URL)
    from app import main as main_module
    importlib.reload(main_module)
    local_app = main_module.create_app()
    with TestClient(local_app) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "openapi" in data
        assert "paths" in data
        assert isinstance(data["paths"], dict)


def test_includes_events_router_does_not_error(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', TEST_DB_URL)
    from app import main as main_module
    importlib.reload(main_module)
    local_app = main_module.create_app()
    # Ensure TestClient can be instantiated without raising errors
    with TestClient(local_app):
        pass
    assert len(local_app.routes) > 0


def test_debug_flag_by_env(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', TEST_DB_URL)
    from app import main as main_module

    monkeypatch.setenv('APP_ENV', 'production')
    importlib.reload(main_module)
    assert main_module.create_app().debug is False

    monkeypatch.setenv('APP_ENV', 'development')
    importlib.reload(main_module)
    assert main_module.create_app().debug is True
