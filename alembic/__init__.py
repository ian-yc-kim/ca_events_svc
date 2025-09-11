from __future__ import annotations

# Local Alembic package to host env.py for tests and migrations.
# We intentionally keep this __init__ minimal. The tests import
# `alembic.env` and also reference `alembic.context` for monkeypatching.
# A lightweight `alembic/context.py` is provided to satisfy those needs.
