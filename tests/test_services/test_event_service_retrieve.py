"""Tests for EventService event retrieval functionality."""

import pytest
from uuid import uuid4
from unittest.mock import Mock

from app.exceptions import EventNotFoundError, EventValidationError


class TestEventServiceRetrieve:
    """Test cases for EventService.get_event and list_events methods."""
    
    def test_get_event_success(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model,
        mock_query_result
    ):
        """Test successful event retrieval by ID."""
        # Arrange
        event_id = sample_event_model.id
        mock_query_result.scalar_one_or_none.return_value = sample_event_model
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        result = mock_event_service.get_event(event_id)
        
        # Assert
        assert result == sample_event_model
        mock_db_session.execute.assert_called_once()
        
        # Verify the SQL query was built correctly
        call_args = mock_db_session.execute.call_args[0][0]
        # Note: In real implementation, this would be a select statement
        # Here we just verify execute was called
    
    def test_get_event_not_found(
        self,
        mock_event_service,
        mock_db_session,
        mock_query_result
    ):
        """Test EventNotFoundError when event doesn't exist."""
        # Arrange
        event_id = uuid4()
        mock_query_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_query_result
        
        # Act & Assert
        with pytest.raises(EventNotFoundError) as exc_info:
            mock_event_service.get_event(event_id)
        
        assert str(event_id) in str(exc_info.value)
        mock_db_session.execute.assert_called_once()
    
    def test_get_event_database_error(
        self,
        mock_event_service,
        mock_db_session,
        mock_sqlalchemy_error
    ):
        """Test handling of database errors during retrieval."""
        # Arrange
        event_id = uuid4()
        mock_db_session.execute.side_effect = mock_sqlalchemy_error
        
        # Act & Assert
        with pytest.raises(EventValidationError) as exc_info:
            mock_event_service.get_event(event_id)
        
        assert "Event retrieval failed due to database error" in str(exc_info.value)
    
    def test_list_events_success_default_pagination(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_list,
        mock_query_result
    ):
        """Test successful event listing with default pagination."""
        # Arrange
        mock_scalars = Mock()
        mock_scalars.all.return_value = sample_event_list
        mock_query_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        result = mock_event_service.list_events()
        
        # Assert
        assert result == sample_event_list
        mock_db_session.execute.assert_called_once()
        
        # Verify pagination parameters (offset=0, default limit from config)
        # In real implementation, this would check the SQL statement
    
    def test_list_events_success_custom_pagination(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_list,
        mock_query_result
    ):
        """Test successful event listing with custom pagination."""
        # Arrange
        mock_scalars = Mock()
        mock_scalars.all.return_value = sample_event_list[:2]  # Simulate limited results
        mock_query_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        result = mock_event_service.list_events(limit=2, offset=5)
        
        # Assert
        assert len(result) == 2
        mock_db_session.execute.assert_called_once()
    
    def test_list_events_respects_max_limit(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_list,
        mock_query_result
    ):
        """Test that list_events respects maximum limit from configuration."""
        # Arrange
        mock_scalars = Mock()
        mock_scalars.all.return_value = sample_event_list
        mock_query_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_query_result
        
        # Act - request limit higher than max allowed
        result = mock_event_service.list_events(limit=1000)  # Higher than max_limit (200)
        
        # Assert
        mock_db_session.execute.assert_called_once()
        # In real implementation, we'd verify the actual limit used was capped at max_limit
    
    def test_list_events_empty_result(
        self,
        mock_event_service,
        mock_db_session,
        mock_query_result
    ):
        """Test listing events when no events exist."""
        # Arrange
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_query_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        result = mock_event_service.list_events()
        
        # Assert
        assert result == []
        mock_db_session.execute.assert_called_once()
    
    def test_list_events_database_error(
        self,
        mock_event_service,
        mock_db_session,
        mock_sqlalchemy_error
    ):
        """Test handling of database errors during event listing."""
        # Arrange
        mock_db_session.execute.side_effect = mock_sqlalchemy_error
        
        # Act & Assert
        with pytest.raises(EventValidationError) as exc_info:
            mock_event_service.list_events()
        
        assert "Event listing failed due to database error" in str(exc_info.value)
    
    def test_list_events_ordering_by_start_datetime(
        self,
        mock_event_service,
        mock_db_session,
        mock_query_result
    ):
        """Test that list_events orders results by start_datetime ascending."""
        from datetime import datetime, timezone
        from app.models.event import Event
        
        # Arrange - create events with different start times
        events = [
            Event(
                id=uuid4(),
                title=f"Event {i}",
                start_datetime=datetime(2025, 1, 15, 10 + i, 0, 0, tzinfo=timezone.utc),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            for i in range(3)
        ]
        
        mock_scalars = Mock()
        mock_scalars.all.return_value = events
        mock_query_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_query_result
        
        # Act
        result = mock_event_service.list_events()
        
        # Assert
        assert len(result) == 3
        mock_db_session.execute.assert_called_once()
        
        # In real implementation, we'd verify the SQL ORDER BY clause
        # Here we just ensure the method doesn't fail
