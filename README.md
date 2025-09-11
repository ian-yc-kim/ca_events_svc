# events-service (FastAPI scaffold)

A lightweight scaffold for the Calendar App's events-service, built with FastAPI. It exposes a FastAPI application with OpenAPI enabled by default and includes a placeholder router mounted at the /events path. The ASGI app import path is app.main:app and the current service version is 0.1.0.

Overview
- Framework: FastAPI
- ASGI app path: app.main:app
- Version: 0.1.0
- OpenAPI: Enabled at /docs (Swagger UI) and /openapi.json
- Routing: Placeholder events router included under /events (no endpoints yet)

Requirements
- Python: 3.11 (per pyproject configuration)
- Dependency management: Poetry

Installation
Dependencies are declared in the Poetry configuration and will be installed via the system's tooling. No manual installation commands are required here.

Configuration
This service uses pydantic-settings (v2-compatible) to load configuration from environment variables and an optional .env file at the project root.

Key points
- Source order: environment variables override values from .env.
- Validation occurs at startup. If required variables are missing or invalid, the application fails fast with a clear error. In code, Pydantic's ValidationError is surfaced as a RuntimeError during app startup.
- Debug mode is automatically toggled based on APP_ENV (debug=True only when development).
- Settings are available at runtime via either:
  - app.state.settings (attached during startup)
  - from app.config import get_settings; settings = get_settings()

Environment variables
- APP_ENV
  - Description: Application environment
  - Allowed values: development, production, test
  - Default: development
  - Behavior: FastAPI debug=True only when development
- HOST
  - Default: 127.0.0.1
  - Validation: Must be a non-empty string
- PORT
  - Default: 8000
  - Validation: Integer in [1..65535]
- DATABASE_URL
  - Required (no default)
  - Validation: Must start with "postgresql://"
  - Security: Never commit secrets. Provide via environment or a secure secret manager
- PAGINATION_DEFAULT_LIMIT
  - Default: 50
  - Validation: Must be > 0
- PAGINATION_MAX_LIMIT
  - Default: 200
  - Validation: Must be >= PAGINATION_DEFAULT_LIMIT

Example .env
Copy the following to a local .env file for development. Replace placeholders with your own values.

```
APP_ENV=development
HOST=127.0.0.1
PORT=8000
DATABASE_URL=postgresql://your_username:your_password@localhost:5432/ca_events
PAGINATION_DEFAULT_LIMIT=50
PAGINATION_MAX_LIMIT=200
```

Notes
- The project depends on pydantic-settings at runtime for configuration loading.
- Database engine/session and logging configuration are out of scope for now and will be added in future tasks.

Running (Development)
Use uvicorn with the application import path app.main:app and enable auto-reload for a smooth development experience.
- Ensure DATABASE_URL is set via environment or .env before starting.
- Example:
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8081
- Notes:
  - --reload is for development only.
  - Binding to 127.0.0.1 is recommended during local development.
  - If you are using Poetry locally, you can optionally prefix commands with: poetry run

Running (Production-like)
Run without --reload and set a non-development APP_ENV to ensure debug mode is disabled.
- Example:
  APP_ENV=production uvicorn app.main:app --host 127.0.0.1 --port 8081
- Notes:
  - Debug is disabled when APP_ENV is anything other than development.
  - Binding to the internal network (127.0.0.1) is recommended by default. Adjust host/port as needed for your environment.

Environment Behavior
- APP_ENV controls the application debug flag.
  - When APP_ENV is unset, it defaults to development (debug=True).
  - Any non-development value (e.g., production) disables debug (debug=False).

OpenAPI Docs
- Interactive docs: /docs
- Raw schema: /openapi.json

Routing Structure
- Routers live under app/routers
- The events router is included and mounted at /events but currently exposes no endpoints. This serves as a placeholder for future event-related APIs.

Next Steps
Future tasks will add:
- CRUD endpoints under /events
- Database integration (PostgreSQL) and migrations
- Structured logging and error handling
- Additional runtime configuration where applicable
