"""Tests for Event Pydantic schemas."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.event import EventCreateSchema, EventUpdateSchema, EventResponseSchema


class TestEventCreateSchema:
    """Test cases for EventCreateSchema."""
    
    def test_valid_complete_payload(self):
        """Test valid complete payload with all fields."""
        data = {
            "title": "Team Meeting",
            "description": "Weekly team sync meeting",
            "start_datetime": "2025-01-15T10:30:00Z",
            "end_datetime": "2025-01-15T11:30:00Z"
        }
        
        event = EventCreateSchema(**data)
        
        assert event.title == "Team Meeting"
        assert event.description == "Weekly team sync meeting"
        assert event.start_datetime == datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert event.end_datetime == datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc)
    
    def test_valid_minimal_payload(self):
        """Test valid minimal payload with only required fields."""
        data = {
            "title": "Meeting",
            "start_datetime": "2025-01-15T10:30:00Z"
        }
        
        event = EventCreateSchema(**data)
        
        assert event.title == "Meeting"
        assert event.description is None
        assert event.start_datetime == datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        assert event.end_datetime is None
    
    def test_valid_various_timezone_formats(self):
        """Test valid datetime inputs with various timezone formats."""
        timezone_cases = [
            ("2025-01-15T10:30:00Z", datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)),
            ("2025-01-15T10:30:00+00:00", datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)),
            ("2025-01-15T15:30:00+05:00", datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)),
            ("2025-01-15T05:30:00-05:00", datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)),
        ]
        
        for input_dt, expected_utc in timezone_cases:
            data = {
                "title": "Meeting",
                "start_datetime": input_dt
            }
            
            event = EventCreateSchema(**data)
            assert event.start_datetime == expected_utc
    
    def test_valid_datetime_object_input(self):
        """Test valid datetime object as input."""
        utc_dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        data = {
            "title": "Meeting",
            "start_datetime": utc_dt
        }
        
        event = EventCreateSchema(**data)
        assert event.start_datetime == utc_dt
    
    def test_title_validation_valid_cases(self):
        """Test title validation with valid inputs."""
        valid_titles = [
            "A",  # 1 character
            "Meeting",  # Normal length
            "A" * 255,  # Maximum length
            "  Meeting  ",  # With whitespace (stripped length > 0)
        ]
        
        for title in valid_titles:
            data = {
                "title": title,
                "start_datetime": "2025-01-15T10:30:00Z"
            }
            
            event = EventCreateSchema(**data)
            assert event.title == title  # Whitespace preserved
    
    def test_title_validation_invalid_cases(self):
        """Test title validation with invalid inputs."""
        invalid_cases = [
            ("", "Title must be between 1 and 255 characters"),
            ("   ", "Title must be between 1 and 255 characters"),  # Only whitespace
            ("A" * 256, "Title must be between 1 and 255 characters"),  # Too long
            (None, "Input should be a valid string"),  # None value - Pydantic type validation
            (123, "Input should be a valid string"),  # Non-string - Pydantic type validation
        ]
        
        for title, expected_error in invalid_cases:
            data = {
                "title": title,
                "start_datetime": "2025-01-15T10:30:00Z"
            }
            
            with pytest.raises(ValidationError) as exc_info:
                EventCreateSchema(**data)
            
            error_messages = [str(error) for error in exc_info.value.errors()]
            assert any(expected_error in msg for msg in error_messages)
    
    def test_description_validation_valid_cases(self):
        """Test description validation with valid inputs."""
        valid_descriptions = [
            None,  # Optional field
            "",  # Empty string
            "Short description",  # Normal length
            "A" * 2000,  # Maximum length
        ]
        
        for description in valid_descriptions:
            data = {
                "title": "Meeting",
                "start_datetime": "2025-01-15T10:30:00Z",
                "description": description
            }
            
            event = EventCreateSchema(**data)
            assert event.description == description
    
    def test_description_validation_invalid_cases(self):
        """Test description validation with invalid inputs."""
        invalid_cases = [
            ("A" * 2001, "Description cannot exceed 2000 characters"),  # Too long
            (123, "Input should be a valid string"),  # Non-string - Pydantic type validation
        ]
        
        for description, expected_error in invalid_cases:
            data = {
                "title": "Meeting",
                "start_datetime": "2025-01-15T10:30:00Z",
                "description": description
            }
            
            with pytest.raises(ValidationError) as exc_info:
                EventCreateSchema(**data)
            
            error_messages = [str(error) for error in exc_info.value.errors()]
            assert any(expected_error in msg for msg in error_messages)
    
    def test_datetime_validation_invalid_cases(self):
        """Test datetime validation with invalid inputs."""
        invalid_cases = [
            ("2025-01-15T10:30:00", "Timezone-naive datetime not allowed"),  # No timezone
            ("invalid-format", "Invalid datetime format"),  # Invalid format
            (None, "Datetime value cannot be None"),  # None for required field
            ("", "Datetime string cannot be empty"),  # Empty string
        ]
        
        for start_dt, expected_error in invalid_cases:
            data = {
                "title": "Meeting",
                "start_datetime": start_dt
            }
            
            with pytest.raises(ValidationError) as exc_info:
                EventCreateSchema(**data)
            
            error_messages = [str(error) for error in exc_info.value.errors()]
            assert any(expected_error in msg for msg in error_messages)
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        # Missing title
        with pytest.raises(ValidationError) as exc_info:
            EventCreateSchema(start_datetime="2025-01-15T10:30:00Z")
        assert "title" in str(exc_info.value)
        
        # Missing start_datetime
        with pytest.raises(ValidationError) as exc_info:
            EventCreateSchema(title="Meeting")
        assert "start_datetime" in str(exc_info.value)


class TestEventUpdateSchema:
    """Test cases for EventUpdateSchema."""
    
    def test_valid_complete_update(self):
        """Test valid update with all fields."""
        data = {
            "title": "Updated Meeting",
            "description": "Updated description",
            "start_datetime": "2025-01-16T10:30:00Z",
            "end_datetime": "2025-01-16T11:30:00Z"
        }
        
        event = EventUpdateSchema(**data)
        
        assert event.title == "Updated Meeting"
        assert event.description == "Updated description"
        assert event.start_datetime == datetime(2025, 1, 16, 10, 30, 0, tzinfo=timezone.utc)
        assert event.end_datetime == datetime(2025, 1, 16, 11, 30, 0, tzinfo=timezone.utc)
    
    def test_valid_partial_updates(self):
        """Test valid partial updates with individual fields."""
        # Only title
        data = {"title": "New Title"}
        event = EventUpdateSchema(**data)
        assert event.title == "New Title"
        assert event.description is None
        assert event.start_datetime is None
        assert event.end_datetime is None
        
        # Only description
        data = {"description": "New Description"}
        event = EventUpdateSchema(**data)
        assert event.description == "New Description"
        assert event.title is None
        
        # Only start_datetime
        data = {"start_datetime": "2025-01-16T10:30:00Z"}
        event = EventUpdateSchema(**data)
        assert event.start_datetime == datetime(2025, 1, 16, 10, 30, 0, tzinfo=timezone.utc)
        
        # Only end_datetime
        data = {"end_datetime": "2025-01-16T11:30:00Z"}
        event = EventUpdateSchema(**data)
        assert event.end_datetime == datetime(2025, 1, 16, 11, 30, 0, tzinfo=timezone.utc)
    
    def test_empty_update(self):
        """Test empty update (all fields None)."""
        event = EventUpdateSchema()
        
        assert event.title is None
        assert event.description is None
        assert event.start_datetime is None
        assert event.end_datetime is None
    
    def test_title_validation_when_provided(self):
        """Test title validation applies when title is provided."""
        # Valid title
        event = EventUpdateSchema(title="Valid Title")
        assert event.title == "Valid Title"
        
        # Invalid title
        with pytest.raises(ValidationError) as exc_info:
            EventUpdateSchema(title="")
        
        error_messages = [str(error) for error in exc_info.value.errors()]
        assert any("Title must be between 1 and 255 characters" in msg for msg in error_messages)
    
    def test_description_validation_when_provided(self):
        """Test description validation applies when description is provided."""
        # Valid description
        event = EventUpdateSchema(description="Valid description")
        assert event.description == "Valid description"
        
        # Invalid description
        with pytest.raises(ValidationError) as exc_info:
            EventUpdateSchema(description="A" * 2001)
        
        error_messages = [str(error) for error in exc_info.value.errors()]
        assert any("Description cannot exceed 2000 characters" in msg for msg in error_messages)
    
    def test_datetime_validation_when_provided(self):
        """Test datetime validation applies when datetime fields are provided."""
        # Valid datetime
        event = EventUpdateSchema(start_datetime="2025-01-16T10:30:00Z")
        assert event.start_datetime == datetime(2025, 1, 16, 10, 30, 0, tzinfo=timezone.utc)
        
        # Invalid datetime
        with pytest.raises(ValidationError) as exc_info:
            EventUpdateSchema(start_datetime="2025-01-16T10:30:00")  # No timezone
        
        error_messages = [str(error) for error in exc_info.value.errors()]
        assert any("Timezone-naive datetime not allowed" in msg for msg in error_messages)
    
    def test_same_validation_rules_as_create(self):
        """Test that update schema uses same validation rules as create schema."""
        # This test ensures consistency between create and update schemas
        create_data = {
            "title": "Test Meeting",
            "description": "Test description",
            "start_datetime": "2025-01-15T10:30:00+05:00",
            "end_datetime": "2025-01-15T11:30:00+05:00"
        }
        
        # Should work for both schemas
        create_event = EventCreateSchema(**create_data)
        update_event = EventUpdateSchema(**create_data)
        
        assert create_event.title == update_event.title
        assert create_event.description == update_event.description
        assert create_event.start_datetime == update_event.start_datetime
        assert create_event.end_datetime == update_event.end_datetime


class TestEventResponseSchema:
    """Test cases for EventResponseSchema."""
    
    def test_valid_response_creation(self):
        """Test creating response schema with all fields."""
        data = {
            "id": uuid4(),
            "title": "Meeting",
            "description": "Team meeting",
            "start_datetime": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "end_datetime": datetime(2025, 1, 15, 11, 30, 0, tzinfo=timezone.utc),
            "created_at": datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc)
        }
        
        response = EventResponseSchema(**data)
        
        assert response.id == data["id"]
        assert response.title == "Meeting"
        assert response.description == "Team meeting"
        assert response.start_datetime == data["start_datetime"]
        assert response.end_datetime == data["end_datetime"]
        assert response.created_at == data["created_at"]
        assert response.updated_at == data["updated_at"]
    
    def test_response_with_optional_fields_none(self):
        """Test response schema with optional fields as None."""
        data = {
            "id": uuid4(),
            "title": "Meeting",
            "description": None,  # Optional field
            "start_datetime": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "end_datetime": None,  # Optional field
            "created_at": datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc)
        }
        
        response = EventResponseSchema(**data)
        
        assert response.description is None
        assert response.end_datetime is None
    
    def test_from_orm_compatibility(self):
        """Test that Config.from_attributes is properly set for ORM conversion."""
        # This test verifies the configuration is set correctly
        # The actual ORM conversion will be tested in integration tests
        assert hasattr(EventResponseSchema.model_config, 'from_attributes') or EventResponseSchema.Config.from_attributes
    
    def test_json_serialization(self):
        """Test JSON serialization with custom encoders."""
        data = {
            "id": uuid4(),
            "title": "Meeting",
            "description": "Team meeting",
            "start_datetime": datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "end_datetime": None,
            "created_at": datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 1, 10, 9, 0, 0, tzinfo=timezone.utc)
        }
        
        response = EventResponseSchema(**data)
        json_str = response.model_dump_json()
        
        # Verify JSON can be parsed
        import json
        json_data = json.loads(json_str)
        
        assert "id" in json_data
        assert "title" in json_data
        assert "start_datetime" in json_data
        assert "created_at" in json_data
        assert "updated_at" in json_data
        
        # Verify datetime serialization format (ISO format)
        assert "T" in json_data["start_datetime"]
        assert json_data["end_datetime"] is None


class TestSchemaIntegration:
    """Integration tests for schema validation."""
    
    def test_create_to_response_conversion(self):
        """Test converting create schema data for use in response schema."""
        create_data = {
            "title": "Team Meeting",
            "description": "Weekly sync",
            "start_datetime": "2025-01-15T10:30:00Z",
            "end_datetime": "2025-01-15T11:30:00Z"
        }
        
        create_schema = EventCreateSchema(**create_data)
        
        # Simulate what would happen in a service layer
        response_data = {
            "id": uuid4(),
            **create_schema.model_dump(),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        response_schema = EventResponseSchema(**response_data)
        
        assert response_schema.title == create_schema.title
        assert response_schema.description == create_schema.description
        assert response_schema.start_datetime == create_schema.start_datetime
        assert response_schema.end_datetime == create_schema.end_datetime
    
    def test_update_partial_data_handling(self):
        """Test that update schema properly handles partial data."""
        # Simulate updating only title and description
        update_data = {
            "title": "Updated Title",
            "description": "Updated description"
            # start_datetime and end_datetime not provided
        }
        
        update_schema = EventUpdateSchema(**update_data)
        update_dict = update_schema.model_dump(exclude_none=True)
        
        # Only provided fields should be in the dict
        assert "title" in update_dict
        assert "description" in update_dict
        assert "start_datetime" not in update_dict
        assert "end_datetime" not in update_dict
    
    def test_error_message_clarity(self):
        """Test that validation error messages are clear and actionable."""
        invalid_data = {
            "title": "",  # Invalid: empty
            "description": "A" * 2001,  # Invalid: too long
            "start_datetime": "2025-01-15T10:30:00",  # Invalid: no timezone
            "end_datetime": "invalid-format"  # Invalid: format
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EventCreateSchema(**invalid_data)
        
        errors = exc_info.value.errors()
        error_messages = [str(error) for error in errors]
        
        # Check that error messages are informative
        assert len(errors) >= 4  # Should have multiple validation errors
        
        # Verify specific error messages are present
        all_messages = " ".join(error_messages)
        assert "Title must be between 1 and 255 characters" in all_messages
        assert "Description cannot exceed 2000 characters" in all_messages
        assert "Timezone-naive datetime not allowed" in all_messages