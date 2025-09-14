from __future__ import annotations

import uuid
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# Import app.models to ensure Event model is registered in Base.metadata
import app.models
from app.models import Base, Event


class TestEventModel:
    """Test Event ORM model metadata, constraints, and indexes."""

    def test_events_table_in_metadata(self):
        """Test that events table is present in Base.metadata.tables after importing app.models."""
        assert "events" in Base.metadata.tables

    def test_event_tablename(self):
        """Test that Event.__tablename__ is 'events'."""
        assert Event.__tablename__ == "events"

    def test_event_columns_presence_and_properties(self):
        """Test column presence and properties for Event model."""
        events_table = Base.metadata.tables["events"]
        columns = events_table.columns

        # Test id column
        id_col = columns["id"]
        assert isinstance(id_col.type, pg.UUID)
        assert id_col.type.as_uuid is True
        assert id_col.primary_key is True
        assert id_col.nullable is False
        assert id_col.default is not None

        # Test title column
        title_col = columns["title"]
        assert isinstance(title_col.type, sa.String)
        assert title_col.type.length == 255
        assert title_col.nullable is False

        # Test description column
        description_col = columns["description"]
        assert isinstance(description_col.type, sa.String)
        assert description_col.type.length == 2000
        assert description_col.nullable is True

        # Test start_datetime column
        start_datetime_col = columns["start_datetime"]
        assert isinstance(start_datetime_col.type, sa.TIMESTAMP)
        assert start_datetime_col.type.timezone is True
        assert start_datetime_col.nullable is False

        # Test end_datetime column
        end_datetime_col = columns["end_datetime"]
        assert isinstance(end_datetime_col.type, sa.TIMESTAMP)
        assert end_datetime_col.type.timezone is True
        assert end_datetime_col.nullable is True

        # Test created_at column
        created_at_col = columns["created_at"]
        assert isinstance(created_at_col.type, sa.TIMESTAMP)
        assert created_at_col.type.timezone is True
        assert created_at_col.nullable is False
        assert created_at_col.server_default is not None

        # Test updated_at column
        updated_at_col = columns["updated_at"]
        assert isinstance(updated_at_col.type, sa.TIMESTAMP)
        assert updated_at_col.type.timezone is True
        assert updated_at_col.nullable is False
        assert updated_at_col.server_default is not None
        assert updated_at_col.onupdate is not None

    def test_check_constraint_end_after_start(self):
        """Test that CheckConstraint 'end_after_start' with correct predicate is attached to the table."""
        events_table = Base.metadata.tables["events"]
        
        # Find the check constraint by name
        check_constraint = None
        for constraint in events_table.constraints:
            if isinstance(constraint, sa.CheckConstraint) and constraint.name == "end_after_start":
                check_constraint = constraint
                break
        
        assert check_constraint is not None, "CheckConstraint 'end_after_start' not found"
        assert check_constraint.name == "end_after_start"
        
        # Check the constraint's SQL text contains the expected condition
        constraint_text = str(check_constraint.sqltext).strip()
        expected_condition = "(end_datetime IS NULL OR end_datetime > start_datetime)"
        assert expected_condition in constraint_text

    def test_start_datetime_index(self):
        """Test that an index named 'ix_events_start_datetime' exists for the start_datetime column."""
        events_table = Base.metadata.tables["events"]
        
        # Find the index by name
        start_datetime_index = None
        for index in events_table.indexes:
            if index.name == "ix_events_start_datetime":
                start_datetime_index = index
                break
        
        assert start_datetime_index is not None, "Index 'ix_events_start_datetime' not found"
        assert start_datetime_index.name == "ix_events_start_datetime"
        
        # Verify the index is on the start_datetime column
        indexed_columns = [col.name for col in start_datetime_index.columns]
        assert "start_datetime" in indexed_columns
        assert start_datetime_index.unique is False

    def test_event_model_instantiation(self):
        """Test that Event model can be instantiated with proper attributes."""
        from datetime import datetime, timezone
        
        event = Event(
            title="Test Event",
            description="Test Description",
            start_datetime=datetime.now(timezone.utc),
            end_datetime=datetime.now(timezone.utc)
        )
        
        assert event.title == "Test Event"
        assert event.description == "Test Description"
        assert event.start_datetime is not None
        assert event.end_datetime is not None
        assert isinstance(event.id, type(None))  # id will be None until saved

    def test_event_repr(self):
        """Test Event model's __repr__ method."""
        from datetime import datetime, timezone
        
        test_id = uuid.uuid4()
        event = Event(
            id=test_id,
            title="Test Event",
            start_datetime=datetime.now(timezone.utc)
        )
        
        repr_str = repr(event)
        assert "Event" in repr_str
        assert str(test_id) in repr_str
        assert "Test Event" in repr_str
