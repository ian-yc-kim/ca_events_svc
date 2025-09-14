"""Test fixtures and configuration for pytest."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, MagicMock

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.event import EventCreateSchema, EventUpdateSchema


# Use the same test database URL as existing tests
TEST_DB_URL = "postgresql://user:pass@localhost:5432/testdb"


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Setup test environment with proper database URL."""
    monkeypatch.setenv("DATABASE_URL", TEST_DB_URL)
    monkeypatch.setenv("APP_ENV", "test")


@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy session for unit testing."""
    session = Mock(spec=Session)
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.refresh = Mock()
    session.delete = Mock()
    session.execute = Mock()
    return session


@pytest.fixture
def mock_event_service(mock_db_session):
    """EventService instance with mocked database session."""
    # Import after environment is set up
    from app.services.event_service import EventService
    return EventService(db_session=mock_db_session)


@pytest.fixture
def sample_event_create_data():
    """Sample event creation data."""
    return {
        "title": "Team Meeting",
        "description": "Weekly team sync meeting",
        "start_datetime": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        "end_datetime": datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc)
    }


@pytest.fixture
def sample_event_create_schema(sample_event_create_data):
    """Sample EventCreateSchema instance."""
    return EventCreateSchema(**sample_event_create_data)


@pytest.fixture
def sample_event_update_data():
    """Sample event update data."""
    return {
        "title": "Updated Meeting",
        "description": "Updated description"
    }


@pytest.fixture
def sample_event_update_schema(sample_event_update_data):
    """Sample EventUpdateSchema instance."""
    return EventUpdateSchema(**sample_event_update_data)


@pytest.fixture
def sample_event_model():
    """Sample Event model instance."""
    return Event(
        id=uuid4(),
        title="Team Meeting",
        description="Weekly team sync meeting",
        start_datetime=datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        end_datetime=datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc)
    )


@pytest.fixture
def sample_event_list():
    """Sample list of Event model instances."""
    return [
        Event(
            id=uuid4(),
            title=f"Meeting {i}",
            description=f"Description {i}",
            start_datetime=datetime(2025, 1, 15, 10 + i, 30, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 1, 15, 11 + i, 30, 0, tzinfo=timezone.utc),
            created_at=datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc)
        )
        for i in range(3)
    ]


@pytest.fixture
def mock_integrity_error():
    """Mock IntegrityError for testing database constraint violations."""
    return IntegrityError(
        "(psycopg2.errors.CheckViolation) new row for relation violates check constraint",
        params=None,
        orig=Mock()
    )


@pytest.fixture
def mock_sqlalchemy_error():
    """Mock SQLAlchemyError for testing general database errors."""
    return SQLAlchemyError("Database connection error")


@pytest.fixture
def mock_query_result():
    """Mock query result for database operations."""
    result = Mock()
    result.scalar_one_or_none = Mock()
    result.scalars = Mock()
    return result
