"""Tests for EventService error handling and edge cases."""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.exceptions import EventBusinessRuleError, EventValidationError, EventNotFoundError
from app.services.event_service import EventService


class TestEventServiceErrorHandling:
    """Test cases for EventService error handling and edge cases."""
    
    def test_business_rule_validation_edge_case_microseconds(
        self,
        mock_event_service
    ):
        """Test business rule validation with microsecond precision."""
        # Arrange - times that are very close but end is still after start
        start_time = datetime(2025, 1, 15, 10, 30, 0, 1, tzinfo=timezone.utc)  # .000001 seconds
        end_time = datetime(2025, 1, 15, 10, 30, 0, 2, tzinfo=timezone.utc)    # .000002 seconds
        
        event_data = {
            "start_datetime": start_time,
            "end_datetime": end_time,
            "title": "Test Event",
            "description": "Test"
        }
        
        # Act & Assert - should not raise exception
        mock_event_service._validate_business_rules(event_data)
    
    def test_business_rule_validation_missing_fields(
        self,
        mock_event_service
    ):
        """Test business rule validation with missing datetime fields."""
        # Arrange - data with only title
        event_data = {
            "title": "Test Event",
            "description": "Test"
        }
        
        # Act & Assert - should not raise exception when datetime fields are missing
        mock_event_service._validate_business_rules(event_data)
    
    def test_business_rule_validation_none_values(
        self,
        mock_event_service
    ):
        """Test business rule validation with None datetime values."""
        # Arrange
        event_data = {
            "start_datetime": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "end_datetime": None,
            "title": "Test Event",
            "description": "Test"
        }
        
        # Act & Assert - should not raise exception when end_datetime is None
        mock_event_service._validate_business_rules(event_data)
    
    def test_business_rule_validation_start_none_end_provided(
        self,
        mock_event_service
    ):
        """Test business rule validation when start is None but end is provided."""
        # Arrange - unusual case where start is None but end is provided
        event_data = {
            "start_datetime": None,
            "end_datetime": datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc),
            "title": "Test Event",
            "description": "Test"
        }
        
        # Act & Assert - should not raise exception (business rules only validate when both are present)
        mock_event_service._validate_business_rules(event_data)
    
    def test_service_initialization_with_none_session(
        self
    ):
        """Test EventService initialization with None session."""
        # Act & Assert - should not raise exception during initialization
        service = EventService(db_session=None)
        assert service.db_session is None
    
    def test_logging_integration_success_operations(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_schema,
        sample_event_model
    ):
        """Test that successful operations include appropriate logging."""
        # Note: This test verifies the service doesn't fail when logging is called
        # In a real implementation, you might want to capture and verify log messages
        
        with patch('app.services.event_service.logging.info') as mock_log_info:
            # Act - perform operations that should trigger info logging
            mock_event_service.create_event(sample_event_create_schema)
            
            # Assert - logging was called (in real implementation, we'd verify message content)
            mock_log_info.assert_called()
    
    def test_logging_integration_error_operations(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_create_schema,
        mock_sqlalchemy_error
    ):
        """Test that error operations include appropriate error logging."""
        # Arrange
        mock_db_session.commit.side_effect = mock_sqlalchemy_error
        
        with patch('app.services.event_service.logging.error') as mock_log_error:
            # Act & Assert
            with pytest.raises(EventValidationError):
                mock_event_service.create_event(sample_event_create_schema)
            
            # Assert - error logging was called with exc_info=True
            mock_log_error.assert_called()
            call_args = mock_log_error.call_args
            assert call_args[1]['exc_info'] is True
    
    def test_configuration_integration(
        self,
        mock_event_service
    ):
        """Test that service properly integrates with configuration settings."""
        # Act
        settings = mock_event_service.settings
        
        # Assert - settings should be available
        assert settings is not None
        assert hasattr(settings, 'pagination_default_limit')
        assert hasattr(settings, 'pagination_max_limit')
    
    def test_uuid_handling_in_exceptions(
        self
    ):
        """Test that UUID values are properly handled in exception messages."""
        # Arrange
        test_uuid = uuid4()
        
        # Act
        exception = EventNotFoundError(str(test_uuid))
        
        # Assert
        assert str(test_uuid) in str(exception)
        assert str(test_uuid) in exception.message
        assert exception.event_id == str(test_uuid)
    
    def test_exception_hierarchy(
        self
    ):
        """Test that custom exceptions maintain proper inheritance hierarchy."""
        # Arrange & Act
        not_found = EventNotFoundError("test-id")
        validation_error = EventValidationError("validation failed")
        business_rule_error = EventBusinessRuleError("business rule violated")
        
        # Assert - all should be instances of base exception
        from app.exceptions import EventBaseError
        assert isinstance(not_found, EventBaseError)
        assert isinstance(validation_error, EventBaseError)
        assert isinstance(business_rule_error, EventBaseError)
        
        # And all should be standard Python exceptions
        assert isinstance(not_found, Exception)
        assert isinstance(validation_error, Exception)
        assert isinstance(business_rule_error, Exception)
    
    def test_service_method_transaction_isolation(
        self,
        mock_event_service,
        mock_db_session,
        mock_sqlalchemy_error
    ):
        """Test that each service method properly handles its own transaction."""
        from app.schemas.event import EventCreateSchema
        
        # Arrange - first operation fails
        mock_db_session.commit.side_effect = mock_sqlalchemy_error
        
        invalid_data = {
            "title": "Test",
            "start_datetime": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        }
        schema = EventCreateSchema(**invalid_data)
        
        # Act & Assert - first operation fails and rolls back
        with pytest.raises(EventValidationError):
            mock_event_service.create_event(schema)
        
        mock_db_session.rollback.assert_called_once()
        
        # Reset mock for next operation
        mock_db_session.reset_mock()
        mock_db_session.commit.side_effect = None  # Remove the error for next call
        
        # Second operation should not be affected by the first failure
        result = mock_event_service.create_event(schema)
        mock_db_session.add.assert_called_once()
    
    def test_pagination_edge_cases(
        self,
        mock_event_service,
        mock_db_session,
        mock_query_result
    ):
        """Test edge cases in pagination handling."""
        # Arrange
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_query_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_query_result
        
        # Test negative offset (should still work)
        result = mock_event_service.list_events(limit=10, offset=-1)
        assert result == []
        
        # Test zero limit
        result = mock_event_service.list_events(limit=0, offset=0)
        assert result == []
        
        # Test very large offset
        result = mock_event_service.list_events(limit=10, offset=1000000)
        assert result == []
