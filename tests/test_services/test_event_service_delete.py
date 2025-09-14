"""Tests for EventService event deletion functionality."""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch

from app.exceptions import EventNotFoundError, EventValidationError


class TestEventServiceDelete:
    """Test cases for EventService.delete_event method."""
    
    def test_delete_event_success(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test successful event deletion."""
        # Arrange
        event_id = sample_event_model.id
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act
            result = mock_event_service.delete_event(event_id)
        
        # Assert
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_event_model)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_event_not_found(
        self,
        mock_event_service
    ):
        """Test deletion of non-existent event."""
        # Arrange
        event_id = uuid4()
        
        with patch.object(mock_event_service, 'get_event', side_effect=EventNotFoundError(str(event_id))):
            # Act & Assert
            with pytest.raises(EventNotFoundError):
                mock_event_service.delete_event(event_id)
    
    def test_delete_event_database_integrity_error(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model,
        mock_integrity_error
    ):
        """Test handling of database integrity errors during deletion (e.g., foreign key constraints)."""
        # Arrange
        event_id = sample_event_model.id
        mock_db_session.commit.side_effect = mock_integrity_error
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(EventValidationError) as exc_info:
                mock_event_service.delete_event(event_id)
        
        assert "Event deletion failed due to database constraints" in str(exc_info.value)
        assert "foreign key references" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_delete_event_database_general_error(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model,
        mock_sqlalchemy_error
    ):
        """Test handling of general database errors during deletion."""
        # Arrange
        event_id = sample_event_model.id
        mock_db_session.commit.side_effect = mock_sqlalchemy_error
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(EventValidationError) as exc_info:
                mock_event_service.delete_event(event_id)
        
        assert "Event deletion failed due to database error" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_delete_event_unexpected_error_rollback(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test that unexpected errors during deletion trigger rollback."""
        # Arrange
        event_id = sample_event_model.id
        mock_db_session.commit.side_effect = Exception("Unexpected deletion error")
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                mock_event_service.delete_event(event_id)
        
        assert "Unexpected deletion error" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_delete_event_verifies_existence_first(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test that delete_event calls get_event first to verify existence."""
        # Arrange
        event_id = sample_event_model.id
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model) as mock_get:
            # Act
            result = mock_event_service.delete_event(event_id)
        
        # Assert
        mock_get.assert_called_once_with(event_id)
        mock_db_session.delete.assert_called_once_with(sample_event_model)
    
    def test_delete_event_rollback_on_delete_operation_error(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test rollback when the delete operation itself fails."""
        # Arrange
        event_id = sample_event_model.id
        mock_db_session.delete.side_effect = Exception("Delete operation failed")
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                mock_event_service.delete_event(event_id)
        
        assert "Delete operation failed" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_delete_event_successful_transaction_flow(
        self,
        mock_event_service,
        mock_db_session,
        sample_event_model
    ):
        """Test complete successful transaction flow for event deletion."""
        # Arrange
        event_id = sample_event_model.id
        
        with patch.object(mock_event_service, 'get_event', return_value=sample_event_model):
            # Act
            result = mock_event_service.delete_event(event_id)
        
        # Assert complete flow
        assert result is True
        
        # Verify transaction operations in correct order
        mock_db_session.delete.assert_called_once_with(sample_event_model)
        mock_db_session.commit.assert_called_once()
        
        # No rollback should be called in success case
        mock_db_session.rollback.assert_not_called()
