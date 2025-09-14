"""Tests for error response schemas."""

import json
import pytest
from pydantic import ValidationError

from app.schemas.error import ErrorResponse, ErrorDetail


class TestErrorDetail:
    """Tests for ErrorDetail model."""
    
    def test_error_detail_creation_success(self):
        """Test successful creation of ErrorDetail with valid data."""
        detail = ErrorDetail(field="email", message="Invalid email format")
        
        assert detail.field == "email"
        assert detail.message == "Invalid email format"
    
    def test_error_detail_serialization(self):
        """Test ErrorDetail serialization to dict and JSON."""
        detail = ErrorDetail(field="password", message="Password too short")
        
        # Test model_dump()
        detail_dict = detail.model_dump()
        expected = {"field": "password", "message": "Password too short"}
        assert detail_dict == expected
        
        # Test model_dump_json()
        detail_json = detail.model_dump_json()
        assert json.loads(detail_json) == expected
    
    def test_error_detail_missing_field(self):
        """Test ErrorDetail validation fails when field is missing."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorDetail(message="Missing field name")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "field" in str(errors[0]["loc"])
    
    def test_error_detail_missing_message(self):
        """Test ErrorDetail validation fails when message is missing."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorDetail(field="username")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "message" in str(errors[0]["loc"])
    
    def test_error_detail_empty_strings(self):
        """Test ErrorDetail accepts empty strings for field and message."""
        detail = ErrorDetail(field="", message="")
        
        assert detail.field == ""
        assert detail.message == ""
    
    def test_error_detail_non_string_field(self):
        """Test ErrorDetail validation fails with non-string field."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorDetail(field=123, message="Invalid field type")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
    
    def test_error_detail_non_string_message(self):
        """Test ErrorDetail validation fails with non-string message."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorDetail(field="test_field", message=456)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"


class TestErrorResponse:
    """Tests for ErrorResponse model."""
    
    def test_error_response_creation_success(self):
        """Test successful creation of ErrorResponse with all fields."""
        response = ErrorResponse(
            code="event_not_found",
            message="Event with ID 'abc-123' not found",
            details="Additional error context"
        )
        
        assert response.code == "event_not_found"
        assert response.message == "Event with ID 'abc-123' not found"
        assert response.details == "Additional error context"
    
    def test_error_response_creation_without_details(self):
        """Test successful creation of ErrorResponse without optional details."""
        response = ErrorResponse(
            code="validation_error",
            message="Request validation failed"
        )
        
        assert response.code == "validation_error"
        assert response.message == "Request validation failed"
        assert response.details is None
    
    def test_error_response_serialization_with_details(self):
        """Test ErrorResponse serialization with details field."""
        response = ErrorResponse(
            code="event_validation_error",
            message="Event validation failed",
            details='{"validation_errors": [{"field": "title", "message": "Required field missing"}]}'
        )
        
        # Test model_dump()
        response_dict = response.model_dump()
        expected = {
            "code": "event_validation_error",
            "message": "Event validation failed",
            "details": '{"validation_errors": [{"field": "title", "message": "Required field missing"}]}'
        }
        assert response_dict == expected
        
        # Test model_dump_json()
        response_json = response.model_dump_json()
        assert json.loads(response_json) == expected
    
    def test_error_response_serialization_without_details(self):
        """Test ErrorResponse serialization without details field."""
        response = ErrorResponse(
            code="internal_server_error",
            message="An internal server error occurred"
        )
        
        # Test model_dump()
        response_dict = response.model_dump()
        expected = {
            "code": "internal_server_error",
            "message": "An internal server error occurred",
            "details": None
        }
        assert response_dict == expected
    
    def test_error_response_serialization_exclude_none(self):
        """Test ErrorResponse serialization excluding None values."""
        response = ErrorResponse(
            code="event_not_found",
            message="Event not found"
        )
        
        # Test model_dump() excluding None values
        response_dict = response.model_dump(exclude_none=True)
        expected = {
            "code": "event_not_found",
            "message": "Event not found"
        }
        assert response_dict == expected
        assert "details" not in response_dict
    
    def test_error_response_missing_code(self):
        """Test ErrorResponse validation fails when code is missing."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(message="Missing error code")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "code" in str(errors[0]["loc"])
    
    def test_error_response_missing_message(self):
        """Test ErrorResponse validation fails when message is missing."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(code="test_error")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "message" in str(errors[0]["loc"])
    
    def test_error_response_non_string_code(self):
        """Test ErrorResponse validation fails with non-string code."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(code=404, message="Not found")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
    
    def test_error_response_non_string_message(self):
        """Test ErrorResponse validation fails with non-string message."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(code="test_error", message=123)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
    
    def test_error_response_non_string_details(self):
        """Test ErrorResponse validation fails with non-string details."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse(code="test_error", message="Test message", details=123)
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
    
    def test_error_response_empty_strings(self):
        """Test ErrorResponse accepts empty strings for required fields."""
        response = ErrorResponse(code="", message="", details="")
        
        assert response.code == ""
        assert response.message == ""
        assert response.details == ""
    
    def test_error_response_json_schema_example(self):
        """Test that ErrorResponse example from Config matches expected structure."""
        # This test verifies the example in the Config class is valid
        example_data = {
            "code": "event_not_found",
            "message": "Event with ID 'abc-123' not found",
            "details": None
        }
        
        response = ErrorResponse(**example_data)
        assert response.code == "event_not_found"
        assert response.message == "Event with ID 'abc-123' not found"
        assert response.details is None
