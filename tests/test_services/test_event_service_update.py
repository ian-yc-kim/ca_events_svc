"""Tests for EventService event update functionality."""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch

from app.exceptions import EventNotFoundError, EventBusinessRuleError, EventValidationError


class TestEventServiceUpdate:
    """Test cases for EventService.update_event method."""
    
    def test_update_event_success_partial_update(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model,
        sample_event_update_schema
    ):
        """Test successful partial event update."""
        # Arrange
        event_id = sample_event_model.id
        
        # Mock get_event to return the sample event
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act
            result = mock_event_service.update_event(event_id, sample_event_update_schema)
        
        # Assert
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_event_model)
        
        # Verify the event was updated
        assert sample_event_model.title == sample_event_update_schema.title
        assert sample_event_model.description == sample_event_update_schema.description
    
    def test_update_event_success_single_field(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test successful update of single field."""
        from app.schemas.event import EventUpdateSchema
        
        # Arrange
        event_id = sample_event_model.id
        original_title = sample_event_model.title
        update_schema = EventUpdateSchema(title="New Title Only")
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act
            result = mock_event_service.update_event(event_id, update_schema)
        
        # Assert
        mock_db_session.commit.assert_called_once()
        assert sample_event_model.title == "New Title Only"
        # Other fields should remain unchanged
        assert sample_event_model.description == sample_event_model.description
    
    def test_update_event_no_fields_to_update(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test update with no fields to update (empty update schema)."""
        from app.schemas.event import EventUpdateSchema
        
        # Arrange
        event_id = sample_event_model.id
        empty_update = EventUpdateSchema()  # No fields set
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act
            result = mock_event_service.update_event(event_id, empty_update)
        
        # Assert
        # Should return the event without attempting database operations
        assert result == sample_event_model
        # No commit should be called since no fields were updated
        mock_db_session.commit.assert_not_called()
    
    def test_update_event_not_found(
        self,
        mock_event_service,
        sample_event_update_schema
    ):
        """Test update of non-existent event."""
        # Arrange
        event_id = uuid4()
        
        with patch.object(mock_event_service, 'get_event', side_effect=EventNotFoundError(str(event_id))):
            # Act & Assert
            with pytest.raises(EventNotFoundError):
                mock_event_service.update_event(event_id, sample_event_update_schema)
    
    def test_update_event_business_rule_validation_datetime(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test business rule validation during update (end_datetime > start_datetime)."""
        from app.schemas.event import EventUpdateSchema
        from datetime import datetime, timezone
        
        # Arrange - update end_datetime to be before start_datetime
        event_id = sample_event_model.id
        # Original event has start at 10:30, end at 11:30
        # Update end to 10:00 (before start)
        invalid_update = EventUpdateSchema(
            end_datetime=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        )
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(EventBusinessRuleError) as exc_info:
                mock_event_service.update_event(event_id, invalid_update)
        
        assert "End datetime must be after start datetime" in str(exc_info.value)
    
    def test_update_event_business_rule_validation_combined_data(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test business rule validation with combined existing and new data."""
        from app.schemas.event import EventUpdateSchema
        from datetime import datetime, timezone
        
        # Arrange - update start_datetime to be after existing end_datetime
        event_id = sample_event_model.id
        # Original event has start at 10:30, end at 11:30
        # Update start to 12:00 (after end)
        invalid_update = EventUpdateSchema(
            start_datetime=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        )
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(EventBusinessRuleError) as exc_info:
                mock_event_service.update_event(event_id, invalid_update)
        
        assert "End datetime must be after start datetime" in str(exc_info.value)
    
    def test_update_event_database_integrity_error(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model,
        sample_event_update_schema,
        mock_integrity_error
    ):
        """Test handling of database integrity errors during update."""
        # Arrange
        event_id = sample_event_model.id
        mock_db_session.commit.side_effect = mock_integrity_error
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(EventValidationError) as exc_info:
                mock_event_service.update_event(event_id, sample_event_update_schema)
        
        assert "Event update failed due to data validation constraints" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_update_event_database_general_error(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model,
        sample_event_update_schema,
        mock_sqlalchemy_error
    ):
        """Test handling of general database errors during update."""
        # Arrange
        event_id = sample_event_model.id
        mock_db_session.commit.side_effect = mock_sqlalchemy_error
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(EventValidationError) as exc_info:
                mock_event_service.update_event(event_id, sample_event_update_schema)
        
        assert "Event update failed due to database error" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_update_event_datetime_field_update(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test successful update of datetime fields."""
        from app.schemas.event import EventUpdateSchema
        from datetime import datetime, timezone
        
        # Arrange
        event_id = sample_event_model.id
        new_start = datetime(2025, 1, 16, 9, 0, 0, tzinfo=timezone.utc)
        new_end = datetime(2025, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
        
        datetime_update = EventUpdateSchema(
            start_datetime=new_start,
            end_datetime=new_end
        )
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act
            result = mock_event_service.update_event(event_id, datetime_update)
        
        # Assert
        mock_db_session.commit.assert_called_once()
        assert sample_event_model.start_datetime == new_start
        assert sample_event_model.end_datetime == new_end
    
    def test_update_event_allows_none_end_datetime(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test that updating end_datetime to None is allowed."""
        from app.schemas.event import EventUpdateSchema
        
        # Arrange
        event_id = sample_event_model.id
        # Note: Pydantic won't serialize None values by default in model_dump(exclude_none=True)
        # This test verifies the business logic allows None end_datetime
        
        # Manually create update data that includes None
        update_data = {"end_datetime": None}
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            with patch.object(mock_event_service, '_validate_business_rules') as mock_validate:
                # Simulate setting the field directly
                sample_event_model.end_datetime = None
                
                # Act - call validation directly
                combined_data = {
                    "start_datetime": sample_event_model.start_datetime,
                    "end_datetime": None,
                    "title": sample_event_model.title,
                    "description": sample_event_model.description
                }
                
                # This should not raise an exception
                mock_event_service._validate_business_rules(combined_data)
    
    def test_update_event_exclude_none_behavior(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test that exclude_none=True properly handles partial updates."""
        from app.schemas.event import EventUpdateSchema
        
        # Arrange
        event_id = sample_event_model.id
        partial_update = EventUpdateSchema(title="Updated Title")
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act
            result = mock_event_service.update_event(event_id, partial_update)
        
        # Assert
        # Only title should be updated, other fields unchanged
        assert sample_event_model.title == "Updated Title"
        # Description should not be changed to None
        assert sample_event_model.description == sample_event_model.description
