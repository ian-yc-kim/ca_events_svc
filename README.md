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

Running (Development)
Use uvicorn with the application import path app.main:app and enable auto-reload for a smooth development experience.
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
- Configuration management and environment-specific settings
