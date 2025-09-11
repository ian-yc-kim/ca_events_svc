from importlib import reload


def test_app_factory_defaults(monkeypatch):
    # Ensure APP_ENV is not set so default is development
    monkeypatch.delenv("APP_ENV", raising=False)
    from app import main
    reload(main)
    app = main.create_app()
    assert app.title == "events-service"
    assert app.version == "0.1.0"
    assert app.debug is True  # default is development
    assert app.docs_url == "/docs"
    assert app.openapi_url == "/openapi.json"


def test_app_factory_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    from app import main
    reload(main)
    app = main.create_app()
    assert app.debug is False
