from __future__ import annotations

import os
from pathlib import Path


def test_events_migration_file_exists() -> None:
    path = Path("alembic/versions/0002_create_events_table.py")
    assert path.exists(), "Expected migration 0002_create_events_table.py to exist"


def test_events_migration_contains_create_table_and_columns() -> None:
    path = Path("alembic/versions/0002_create_events_table.py")
    content = path.read_text(encoding="utf-8")

    # Create table
    assert "op.create_table(\n        \"events\"," in content or "op.create_table(\"events\"" in content

    # Columns and types
    assert "sa.Column(\"id\", pg.UUID(as_uuid=True), primary_key=True, nullable=False)" in content
    assert "sa.Column(\"title\", sa.String(length=255), nullable=False)" in content
    assert "sa.Column(\"description\", sa.String(length=2000), nullable=True)" in content
    assert "sa.Column(\"start_datetime\", sa.TIMESTAMP(timezone=True), nullable=False)" in content
    assert "sa.Column(\"end_datetime\", sa.TIMESTAMP(timezone=True), nullable=True)" in content
    assert "sa.Column(\"created_at\", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text(\"now()\"))" in content
    assert "sa.Column(\"updated_at\", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text(\"now()\"))" in content


def test_events_migration_contains_check_constraint() -> None:
    path = Path("alembic/versions/0002_create_events_table.py")
    content = path.read_text(encoding="utf-8")

    expected = "sa.CheckConstraint(\"(end_datetime IS NULL OR end_datetime > start_datetime)\", name=\"end_after_start\")"
    assert expected in content, "Expected check constraint with exact name and predicate"


def test_events_migration_contains_index() -> None:
    path = Path("alembic/versions/0002_create_events_table.py")
    content = path.read_text(encoding="utf-8")

    expected_idx = "op.create_index(\n        \"ix_events_start_datetime\",\n        \"events\",\n        [\"start_datetime\"],\n        unique=False,\n    )"
    # Be tolerant to spacing but ensure the key parts exist
    assert "op.create_index(" in content
    assert "\"ix_events_start_datetime\"" in content
    assert "\"events\"" in content
    assert "[\"start_datetime\"]" in content
    assert "unique=False" in content


def test_events_migration_has_correct_revisions() -> None:
    path = Path("alembic/versions/0002_create_events_table.py")
    content = path.read_text(encoding="utf-8")

    assert 'revision = "0002_create_events_table"' in content
    assert 'down_revision = "0001"' in content
