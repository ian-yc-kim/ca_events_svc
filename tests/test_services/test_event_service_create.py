"""Tests for EventService event creation functionality."""

import pytest
from uuid import uuid4
from unittest.mock import Mock

from app.exceptions import EventBusinessRuleError, EventValidationError
from app.models.event import Event


class TestEventServiceCreate:
    """Test cases for EventService.create_event method."""
    
    def test_create_event_success_complete_data(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_schema
    ):
        """Test successful event creation with complete data."""
        # Arrange
        created_event = Event(
            id=uuid4(),
            title=sample_event_create_schema.title,
            description=sample_event_create_schema.description,
            start_datetime=sample_event_create_schema.start_datetime,
            end_datetime=sample_event_create_schema.end_datetime
        )
        mock_db_session.refresh.side_effect = lambda event: setattr(event, 'id', created_event.id)
        
        # Act
        result = mock_event_service.create_event(sample_event_create_schema)
        
        # Assert
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        
        added_event = mock_db_session.add.call_args[0][0]
        assert isinstance(added_event, Event)
        assert added_event.title == sample_event_create_schema.title
        assert added_event.description == sample_event_create_schema.description
        assert added_event.start_datetime == sample_event_create_schema.start_datetime
        assert added_event.end_datetime == sample_event_create_schema.end_datetime
    
    def test_create_event_success_minimal_data(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_data
    ):
        """Test successful event creation with minimal required data."""
        from app.schemas.event import EventCreateSchema
        
        # Arrange - minimal data (no description, no end_datetime)
        minimal_data = {
            "title": "Meeting",
            "start_datetime": sample_event_create_data["start_datetime"]
        }
        minimal_schema = EventCreateSchema(**minimal_data)
        
        # Act
        result = mock_event_service.create_event(minimal_schema)
        
        # Assert
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        
        added_event = mock_db_session.add.call_args[0][0]
        assert added_event.title == "Meeting"
        assert added_event.description is None
        assert added_event.end_datetime is None
    
    def test_create_event_business_rule_validation_end_before_start(
        self,
        mock_event_service,
        sample_event_create_data
    ):
        """Test business rule validation: end_datetime must be after start_datetime."""
        from app.schemas.event import EventCreateSchema
        from datetime import datetime, timezone
        
        # Arrange - end before start
        invalid_data = sample_event_create_data.copy()
        invalid_data["start_datetime"] = datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc)
        invalid_data["end_datetime"] = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        invalid_schema = EventCreateSchema(**invalid_data)
        
        # Act & Assert
        with pytest.raises(EventBusinessRuleError) as exc_info:
            mock_event_service.create_event(invalid_schema)
        
        assert "End datetime must be after start datetime" in str(exc_info.value)
    
    def test_create_event_business_rule_validation_end_equals_start(
        self,
        mock_event_service,
        sample_event_create_data
    ):
        """Test business rule validation: end_datetime cannot equal start_datetime."""
        from app.schemas.event import EventCreateSchema
        from datetime import datetime, timezone
        
        # Arrange - end equals start
        invalid_data = sample_event_create_data.copy()
        same_time = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        invalid_data["start_datetime"] = same_time
        invalid_data["end_datetime"] = same_time
        
        invalid_schema = EventCreateSchema(**invalid_data)
        
        # Act & Assert
        with pytest.raises(EventBusinessRuleError) as exc_info:
            mock_event_service.create_event(invalid_schema)
        
        assert "End datetime must be after start datetime" in str(exc_info.value)
    
    def test_create_event_business_rule_allows_none_end_datetime(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_data
    ):
        """Test that None end_datetime is allowed (passes business rules)."""
        from app.schemas.event import EventCreateSchema
        
        # Arrange - no end_datetime
        data_without_end = sample_event_create_data.copy()
        del data_without_end["end_datetime"]
        
        schema = EventCreateSchema(**data_without_end)
        
        # Act
        result = mock_event_service.create_event(schema)
        
        # Assert - should not raise business rule error
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_event_database_integrity_error(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_schema,
        mock_integrity_error
    ):
        """Test handling of database integrity constraint violations."""
        # Arrange
        mock_db_session.commit.side_effect = mock_integrity_error
        
        # Act & Assert
        with pytest.raises(EventValidationError) as exc_info:
            mock_event_service.create_event(sample_event_create_schema)
        
        assert "Event creation failed due to data validation constraints" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_create_event_database_general_error(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_schema,
        mock_sqlalchemy_error
    ):
        """Test handling of general database errors."""
        # Arrange
        mock_db_session.commit.side_effect = mock_sqlalchemy_error
        
        # Act & Assert
        with pytest.raises(EventValidationError) as exc_info:
            mock_event_service.create_event(sample_event_create_schema)
        
        assert "Event creation failed due to database error" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_create_event_unexpected_error_rollback(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_schema
    ):
        """Test that unexpected errors trigger rollback."""
        # Arrange
        mock_db_session.commit.side_effect = Exception("Unexpected error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            mock_event_service.create_event(sample_event_create_schema)
        
        assert "Unexpected error" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_create_event_utc_datetime_handling(
        self,
        mock_event_service,
        mock_db_session
    ):
        """Test that UTC datetime values are properly handled."""
        from app.schemas.event import EventCreateSchema
        from datetime import datetime, timezone
        
        # Arrange - use UTC datetimes
        utc_data = {
            "title": "UTC Test Meeting",
            "start_datetime": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc)
        }
        utc_schema = EventCreateSchema(**utc_data)
        
        # Act
        result = mock_event_service.create_event(utc_schema)
        
        # Assert
        added_event = mock_db_session.add.call_args[0][0]
        assert added_event.start_datetime.tzinfo == timezone.utc
        assert added_event.end_datetime.tzinfo == timezone.utc
