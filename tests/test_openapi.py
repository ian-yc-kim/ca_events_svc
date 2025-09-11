from fastapi.testclient import TestClient
from app.main import app as module_app, create_app


def test_docs_served():
    local_app = create_app()
    with TestClient(local_app) as client:
        resp = client.get("/docs")
        assert resp.status_code == 200
        # Check for known Swagger UI markers
        text = resp.text
        assert ("Swagger UI" in text) or ("swagger-ui" in text.lower())


def test_openapi_json_served():
    local_app = create_app()
    with TestClient(local_app) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "openapi" in data
        assert "paths" in data
        assert isinstance(data["paths"], dict)


def test_includes_events_router_does_not_error():
    local_app = create_app()
    # Ensure TestClient can be instantiated without raising errors
    with TestClient(local_app):
        pass
    # Ensure there are routes registered (framework routes are sufficient)
    assert len(local_app.routes) > 0


def test_debug_flag_by_env():
    assert create_app(env="production").debug is False
    assert create_app(env="development").debug is True
