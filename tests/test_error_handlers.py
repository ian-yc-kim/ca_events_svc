"""Tests for exception handler functions."""

import json
import logging
import pytest
from unittest.mock import Mock, patch

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.error_handlers import (
    generate_error_code,
    handle_event_not_found_error,
    handle_event_validation_error,
    handle_event_business_rule_error,
    handle_event_base_error,
    handle_request_validation_error,
    handle_generic_exception,
    _format_validation_errors
)
from app.exceptions import (
    EventBaseError,
    EventNotFoundError,
    EventValidationError,
    EventBusinessRuleError
)


@pytest.fixture
def mock_request():
    """Mock FastAPI Request object for testing handlers."""
    request = Mock(spec=Request)
    request.url = Mock()
    request.url.path = "/test"
    request.method = "GET"
    return request


class TestGenerateErrorCode:
    """Tests for error code generation utility function."""
    
    def test_generate_error_code_event_not_found_error(self):
        """Test error code generation for EventNotFoundError."""
        result = generate_error_code("EventNotFoundError")
        assert result == "event_not_found"
    
    def test_generate_error_code_event_validation_error(self):
        """Test error code generation for EventValidationError."""
        result = generate_error_code("EventValidationError")
        assert result == "event_validation"
    
    def test_generate_error_code_event_business_rule_error(self):
        """Test error code generation for EventBusinessRuleError."""
        result = generate_error_code("EventBusinessRuleError")
        assert result == "event_business_rule"
    
    def test_generate_error_code_event_base_error(self):
        """Test error code generation for EventBaseError."""
        result = generate_error_code("EventBaseError")
        assert result == "event_base"
    
    def test_generate_error_code_request_validation_error(self):
        """Test error code generation for RequestValidationError (special case)."""
        result = generate_error_code("RequestValidationError")
        assert result == "validation_error"
    
    def test_generate_error_code_generic_exception(self):
        """Test error code generation for generic Exception (special case)."""
        result = generate_error_code("Exception")
        assert result == "internal_server_error"
    
    def test_generate_error_code_custom_error_with_suffix(self):
        """Test error code generation for custom error with Error suffix."""
        result = generate_error_code("CustomDatabaseError")
        assert result == "custom_database"
    
    def test_generate_error_code_without_error_suffix(self):
        """Test error code generation for exception without Error suffix."""
        result = generate_error_code("CustomException")
        assert result == "custom_exception"
    
    def test_generate_error_code_single_word(self):
        """Test error code generation for single word exception."""
        result = generate_error_code("TimeoutError")
        assert result == "timeout"
    
    def test_generate_error_code_multiple_camel_case(self):
        """Test error code generation for multiple CamelCase words."""
        result = generate_error_code("DatabaseConnectionTimeoutError")
        assert result == "database_connection_timeout"


class TestFormatValidationErrors:
    """Tests for validation error formatting utility function."""
    
    def test_format_validation_errors_single_error(self):
        """Test formatting single validation error."""
        errors = [
            {"loc": ("title",), "msg": "String too short"}
        ]
        
        result = _format_validation_errors(errors)
        expected = {
            "validation_errors": [
                {"field": "title", "message": "String too short"}
            ]
        }
        
        assert json.loads(result) == expected
    
    def test_format_validation_errors_multiple_errors(self):
        """Test formatting multiple validation errors."""
        errors = [
            {"loc": ("title",), "msg": "String too short"},
            {"loc": ("start_datetime",), "msg": "Invalid datetime format"}
        ]
        
        result = _format_validation_errors(errors)
        expected = {
            "validation_errors": [
                {"field": "title", "message": "String too short"},
                {"field": "start_datetime", "message": "Invalid datetime format"}
            ]
        }
        
        assert json.loads(result) == expected
    
    def test_format_validation_errors_nested_field_path(self):
        """Test formatting validation error with nested field path."""
        errors = [
            {"loc": ("body", "event", "title"), "msg": "Required field missing"}
        ]
        
        result = _format_validation_errors(errors)
        expected = {
            "validation_errors": [
                {"field": "body.event.title", "message": "Required field missing"}
            ]
        }
        
        assert json.loads(result) == expected
    
    def test_format_validation_errors_empty_list(self):
        """Test formatting empty validation errors list."""
        errors = []
        
        result = _format_validation_errors(errors)
        expected = {"validation_errors": []}
        
        assert json.loads(result) == expected
    
    def test_format_validation_errors_missing_loc(self):
        """Test formatting validation error with missing loc field."""
        errors = [
            {"msg": "Validation error"}
        ]
        
        result = _format_validation_errors(errors)
        expected = {
            "validation_errors": [
                {"field": "", "message": "Validation error"}
            ]
        }
        
        assert json.loads(result) == expected
    
    def test_format_validation_errors_missing_msg(self):
        """Test formatting validation error with missing msg field."""
        errors = [
            {"loc": ("title",)}
        ]
        
        result = _format_validation_errors(errors)
        expected = {
            "validation_errors": [
                {"field": "title", "message": "Validation error"}
            ]
        }
        
        assert json.loads(result) == expected


class TestEventNotFoundErrorHandler:
    """Tests for EventNotFoundError handler."""
    
    def test_handle_event_not_found_error_success(self, mock_request):
        """Test successful handling of EventNotFoundError."""
        exc = EventNotFoundError("test-event-id")
        
        response = handle_event_not_found_error(mock_request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_not_found"
        assert error["message"] == "Event with ID 'test-event-id' not found"
        assert error["details"] is None
    
    def test_handle_event_not_found_error_response_structure(self, mock_request):
        """Test EventNotFoundError response follows exact format."""
        exc = EventNotFoundError("abc-123")
        
        response = handle_event_not_found_error(mock_request, exc)
        content = json.loads(response.body.decode())
        
        # Verify exact structure
        assert set(content.keys()) == {"error"}
        assert set(content["error"].keys()) == {"code", "message", "details"}


class TestEventValidationErrorHandler:
    """Tests for EventValidationError handler."""
    
    def test_handle_event_validation_error_success(self, mock_request):
        """Test successful handling of EventValidationError."""
        exc = EventValidationError("Title is required")
        
        response = handle_event_validation_error(mock_request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_validation"
        assert error["message"] == "Title is required"
        assert error["details"] is None
    
    def test_handle_event_validation_error_response_structure(self, mock_request):
        """Test EventValidationError response follows exact format."""
        exc = EventValidationError("Invalid input")
        
        response = handle_event_validation_error(mock_request, exc)
        content = json.loads(response.body.decode())
        
        # Verify exact structure
        assert set(content.keys()) == {"error"}
        assert set(content["error"].keys()) == {"code", "message", "details"}


class TestEventBusinessRuleErrorHandler:
    """Tests for EventBusinessRuleError handler."""
    
    def test_handle_event_business_rule_error_success(self, mock_request):
        """Test successful handling of EventBusinessRuleError."""
        exc = EventBusinessRuleError("Event cannot overlap with existing event")
        
        response = handle_event_business_rule_error(mock_request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400  # Per task requirements
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_business_rule"
        assert error["message"] == "Event cannot overlap with existing event"
        assert error["details"] is None
    
    def test_handle_event_business_rule_error_maps_to_400(self, mock_request):
        """Test EventBusinessRuleError maps to 400 BAD_REQUEST per task requirements."""
        exc = EventBusinessRuleError("Business rule violation")
        
        response = handle_event_business_rule_error(mock_request, exc)
        
        # Verify it maps to 400, not 500
        assert response.status_code == 400


class TestEventBaseErrorHandler:
    """Tests for EventBaseError handler."""
    
    @patch('app.error_handlers.logging.error')
    def test_handle_event_base_error_success(self, mock_logging, mock_request):
        """Test successful handling of EventBaseError."""
        exc = EventBaseError("Unexpected event error")
        
        response = handle_event_base_error(mock_request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        # Verify error logging
        mock_logging.assert_called_once()
        call_args = mock_logging.call_args
        assert "EventBaseError occurred" in call_args[0][0]
        assert call_args[1]['exc_info'] is True
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_base"
        assert error["message"] == "Unexpected event error"
        assert error["details"] is None
    
    @patch('app.error_handlers.logging.error')
    def test_handle_event_base_error_logging(self, mock_logging, mock_request):
        """Test EventBaseError logs 500-level errors for debugging."""
        exc = EventBaseError("Test error")
        
        handle_event_base_error(mock_request, exc)
        
        # Verify structured logging call
        mock_logging.assert_called_once()
        call_args = mock_logging.call_args
        assert "EventBaseError occurred" in call_args[0][0]
        assert "Test error" in call_args[0][0]  # Check exception message is in the log string
        assert call_args[1]['exc_info'] is True


class TestRequestValidationErrorHandler:
    """Tests for RequestValidationError handler."""
    
    def test_handle_request_validation_error_success(self, mock_request):
        """Test successful handling of RequestValidationError."""
        # Create mock RequestValidationError
        errors = [
            {"loc": ("title",), "msg": "String too short"},
            {"loc": ("start_datetime",), "msg": "Invalid datetime format"}
        ]
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = errors
        
        response = handle_request_validation_error(mock_request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "validation_error"
        assert error["message"] == "Request validation failed"
        assert error["details"] is not None
        
        # Parse details JSON
        details = json.loads(error["details"])
        expected_details = {
            "validation_errors": [
                {"field": "title", "message": "String too short"},
                {"field": "start_datetime", "message": "Invalid datetime format"}
            ]
        }
        assert details == expected_details
    
    def test_handle_request_validation_error_empty_errors(self, mock_request):
        """Test RequestValidationError handler with empty error list."""
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = []
        
        response = handle_request_validation_error(mock_request, exc)
        
        assert response.status_code == 400
        
        content = json.loads(response.body.decode())
        error = content["error"]
        
        details = json.loads(error["details"])
        assert details == {"validation_errors": []}
    
    def test_handle_request_validation_error_structured_details(self, mock_request):
        """Test RequestValidationError formats details as structured JSON string."""
        errors = [
            {"loc": ("body", "event", "title"), "msg": "Required field missing"}
        ]
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = errors
        
        response = handle_request_validation_error(mock_request, exc)
        content = json.loads(response.body.decode())
        error = content["error"]
        
        # Verify details is a JSON string
        assert isinstance(error["details"], str)
        
        # Verify details can be parsed as JSON
        details = json.loads(error["details"])
        expected = {
            "validation_errors": [
                {"field": "body.event.title", "message": "Required field missing"}
            ]
        }
        assert details == expected


class TestGenericExceptionHandler:
    """Tests for generic Exception handler."""
    
    @patch('app.error_handlers.logging.error')
    def test_handle_generic_exception_success(self, mock_logging, mock_request):
        """Test successful handling of generic Exception."""
        exc = Exception("Something went wrong")
        
        response = handle_generic_exception(mock_request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        # Verify error logging
        mock_logging.assert_called_once()
        call_args = mock_logging.call_args
        assert "Unhandled exception occurred" in call_args[0][0]
        assert call_args[1]['exc_info'] is True
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "internal_server_error"
        assert error["message"] == "An internal server error occurred"
        assert error["details"] is None
    
    @patch('app.error_handlers.logging.error')
    def test_handle_generic_exception_no_internal_details_leaked(self, mock_logging, mock_request):
        """Test generic Exception doesn't leak internal details to client."""
        exc = Exception("Internal database connection failed with secret info")
        
        response = handle_generic_exception(mock_request, exc)
        
        content = json.loads(response.body.decode())
        error = content["error"]
        
        # Should not contain the actual exception message
        assert error["message"] == "An internal server error occurred"
        assert "database" not in error["message"]
        assert "secret" not in error["message"]
        assert error["details"] is None
    
    @patch('app.error_handlers.logging.error')
    def test_handle_generic_exception_logging(self, mock_logging, mock_request):
        """Test generic Exception logs 500-level errors for debugging."""
        exc = Exception("Test exception")
        
        handle_generic_exception(mock_request, exc)
        
        # Verify structured logging call
        mock_logging.assert_called_once()
        call_args = mock_logging.call_args
        assert "Unhandled exception occurred" in call_args[0][0]
        assert "Test exception" in call_args[0][0]  # Check exception message is in the log string
        assert call_args[1]['exc_info'] is True


class TestHandlerIndependence:
    """Tests for handler function independence and integration readiness."""
    
    def test_handlers_accept_request_and_exception_params(self, mock_request):
        """Test all handlers accept (request, exc) parameters as required by FastAPI."""
        # Test EventNotFoundError handler
        exc1 = EventNotFoundError("test-id")
        response1 = handle_event_not_found_error(mock_request, exc1)
        assert isinstance(response1, JSONResponse)
        
        # Test EventValidationError handler
        exc2 = EventValidationError("validation failed")
        response2 = handle_event_validation_error(mock_request, exc2)
        assert isinstance(response2, JSONResponse)
        
        # Test EventBusinessRuleError handler
        exc3 = EventBusinessRuleError("business rule violated")
        response3 = handle_event_business_rule_error(mock_request, exc3)
        assert isinstance(response3, JSONResponse)
        
        # Test EventBaseError handler
        exc4 = EventBaseError("base error")
        response4 = handle_event_base_error(mock_request, exc4)
        assert isinstance(response4, JSONResponse)
        
        # Test RequestValidationError handler
        exc5 = Mock(spec=RequestValidationError)
        exc5.errors.return_value = []
        response5 = handle_request_validation_error(mock_request, exc5)
        assert isinstance(response5, JSONResponse)
        
        # Test generic Exception handler
        exc6 = Exception("generic error")
        response6 = handle_generic_exception(mock_request, exc6)
        assert isinstance(response6, JSONResponse)
    
    def test_handlers_return_json_response(self, mock_request):
        """Test all handlers return FastAPI JSONResponse for consistent formatting."""
        handlers_and_exceptions = [
            (handle_event_not_found_error, EventNotFoundError("test-id")),
            (handle_event_validation_error, EventValidationError("test")),
            (handle_event_business_rule_error, EventBusinessRuleError("test")),
            (handle_event_base_error, EventBaseError("test")),
            (handle_generic_exception, Exception("test"))
        ]
        
        for handler, exc in handlers_and_exceptions:
            response = handler(mock_request, exc)
            assert isinstance(response, JSONResponse)
            assert hasattr(response, 'status_code')
            assert hasattr(response, 'body')
    
    def test_handlers_can_be_called_independently(self, mock_request):
        """Test handler functions work independently without FastAPI context."""
        # All handlers should work with just mock Request and exception objects
        exc = EventNotFoundError("independent-test")
        
        # Should not raise any exceptions
        response = handle_event_not_found_error(mock_request, exc)
        
        assert response.status_code == 404
        content = json.loads(response.body.decode())
        assert content["error"]["code"] == "event_not_found"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_exception_with_no_message_attribute(self, mock_request):
        """Test handling exception that doesn't have message attribute."""
        # Create custom exception without message attribute
        class CustomError(EventBaseError):
            def __init__(self):
                # Don't call super().__init__() to avoid setting message
                pass
        
        exc = CustomError()
        
        # Should not crash, but might have empty/default message
        response = handle_event_base_error(mock_request, exc)
        assert response.status_code == 500
        
        content = json.loads(response.body.decode())
        # Should have some message, even if empty or default
        assert "message" in content["error"]
    
    def test_request_validation_error_with_complex_nested_errors(self, mock_request):
        """Test RequestValidationError with complex nested field paths."""
        errors = [
            {"loc": ("body", 0, "events", 2, "title"), "msg": "String too short"},
            {"loc": ("query", "limit"), "msg": "Must be positive integer"},
            {"loc": (), "msg": "Root validation error"}
        ]
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = errors
        
        response = handle_request_validation_error(mock_request, exc)
        
        content = json.loads(response.body.decode())
        details = json.loads(content["error"]["details"])
        
        expected_errors = [
            {"field": "body.0.events.2.title", "message": "String too short"},
            {"field": "query.limit", "message": "Must be positive integer"},
            {"field": "", "message": "Root validation error"}
        ]
        
        assert details["validation_errors"] == expected_errors
    
    def test_all_responses_follow_exact_format(self, mock_request):
        """Test all error responses follow exact format specification."""
        test_cases = [
            (handle_event_not_found_error, EventNotFoundError("test")),
            (handle_event_validation_error, EventValidationError("test")),
            (handle_event_business_rule_error, EventBusinessRuleError("test")),
            (handle_event_base_error, EventBaseError("test")),
            (handle_generic_exception, Exception("test"))
        ]
        
        for handler, exc in test_cases:
            response = handler(mock_request, exc)
            content = json.loads(response.body.decode())
            
            # Verify exact format: {"error": {"code": "string", "message": "string", "details?": "string"}}
            assert set(content.keys()) == {"error"}
            
            error = content["error"]
            required_keys = {"code", "message"}
            optional_keys = {"details"}
            
            assert required_keys.issubset(set(error.keys()))
            assert set(error.keys()).issubset(required_keys | optional_keys)
            
            # Verify field types
            assert isinstance(error["code"], str)
            assert isinstance(error["message"], str)
            if "details" in error:
                assert error["details"] is None or isinstance(error["details"], str)
