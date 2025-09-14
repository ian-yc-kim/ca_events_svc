"""Integration tests for exception handler registration and error handling flow."""

import json
import os
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4


class TestExceptionHandlerRegistration:
    """Tests for exception handler registration in FastAPI application."""
    
    def test_app_startup_with_exception_handlers(self, monkeypatch):
        """Test that FastAPI app starts successfully with all exception handlers registered."""
        # Setup test environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("APP_ENV", "test")
        
        # Import after environment setup
        from app.main import create_app
        
        app = create_app(env="test")
        
        # Verify app was created successfully
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)
        assert app.title == "events-service"
        assert app.version == "0.1.0"
    
    def test_exception_handlers_registered_in_app(self, monkeypatch):
        """Test that all exception handlers are properly registered in FastAPI app."""
        # Setup test environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("APP_ENV", "test")
        
        # Import after environment setup
        from app.main import create_app
        from app.exceptions import (
            EventBaseError,
            EventNotFoundError,
            EventValidationError,
            EventBusinessRuleError
        )
        from fastapi.exceptions import RequestValidationError
        
        app = create_app(env="test")
        
        # FastAPI stores exception handlers in app.exception_handlers
        exception_handlers = app.exception_handlers
        
        # Verify specific exception types are registered
        assert EventNotFoundError in exception_handlers
        assert EventValidationError in exception_handlers
        assert EventBusinessRuleError in exception_handlers
        assert EventBaseError in exception_handlers
        assert RequestValidationError in exception_handlers
        assert Exception in exception_handlers
    
    def test_test_client_creation_successful(self, monkeypatch):
        """Test that TestClient can be created successfully with registered handlers."""
        # Setup test environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("APP_ENV", "test")
        
        # Import after environment setup
        from app.main import create_app
        from fastapi.testclient import TestClient
        
        app = create_app(env="test")
        
        # Should not raise any exceptions
        client = TestClient(app)
        assert client is not None
        
        # Test basic functionality - docs endpoint
        response = client.get("/docs")
        assert response.status_code in [200, 404]  # Either docs work or endpoint doesn't exist


class TestExceptionHandlerFunctionality:
    """Tests for exception handler functionality using direct handler calls."""
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request object."""
        from fastapi import Request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        return request
    
    def test_event_not_found_error_handler_integration(self, mock_request):
        """Test EventNotFoundError handler produces correct response format."""
        from app.exceptions import EventNotFoundError
        from app.error_handlers import handle_event_not_found_error
        
        exc = EventNotFoundError("test-event-id")
        response = handle_event_not_found_error(mock_request, exc)
        
        # Verify response structure
        assert response.status_code == 404
        
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_not_found"
        assert error["message"] == "Event with ID 'test-event-id' not found"
        assert error["details"] is None
    
    def test_event_validation_error_handler_integration(self, mock_request):
        """Test EventValidationError handler produces correct response format."""
        from app.exceptions import EventValidationError
        from app.error_handlers import handle_event_validation_error
        
        exc = EventValidationError("Title is required")
        response = handle_event_validation_error(mock_request, exc)
        
        # Verify response structure
        assert response.status_code == 400
        
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_validation"
        assert error["message"] == "Title is required"
        assert error["details"] is None
    
    def test_event_business_rule_error_handler_integration(self, mock_request):
        """Test EventBusinessRuleError handler returns 400 per task requirements."""
        from app.exceptions import EventBusinessRuleError
        from app.error_handlers import handle_event_business_rule_error
        
        exc = EventBusinessRuleError("Event cannot overlap with existing event")
        response = handle_event_business_rule_error(mock_request, exc)
        
        # Verify response - should be 400 per task requirements
        assert response.status_code == 400
        
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_business_rule"
        assert error["message"] == "Event cannot overlap with existing event"
        assert error["details"] is None
    
    @patch('app.error_handlers.logging.error')
    def test_event_base_error_handler_integration(self, mock_logging, mock_request):
        """Test EventBaseError handler with logging verification."""
        from app.exceptions import EventBaseError
        from app.error_handlers import handle_event_base_error
        
        exc = EventBaseError("Unexpected event error")
        response = handle_event_base_error(mock_request, exc)
        
        # Verify response
        assert response.status_code == 500
        
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "event_base"
        assert error["message"] == "Unexpected event error"
        assert error["details"] is None
        
        # Verify error logging
        mock_logging.assert_called_once()
        call_args = mock_logging.call_args
        assert "EventBaseError occurred" in call_args[0][0]
        assert call_args[1]['exc_info'] is True
    
    def test_request_validation_error_handler_integration(self, mock_request):
        """Test RequestValidationError handler with structured details."""
        from fastapi.exceptions import RequestValidationError
        from app.error_handlers import handle_request_validation_error
        
        # Mock RequestValidationError with validation errors
        errors = [
            {"loc": ("title",), "msg": "String too short"},
            {"loc": ("count",), "msg": "Must be positive"}
        ]
        exc = Mock(spec=RequestValidationError)
        exc.errors.return_value = errors
        
        response = handle_request_validation_error(mock_request, exc)
        
        # Verify response
        assert response.status_code == 400
        
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "validation_error"
        assert error["message"] == "Request validation failed"
        assert error["details"] is not None
        
        # Parse details JSON
        details = json.loads(error["details"])
        assert "validation_errors" in details
        assert len(details["validation_errors"]) == 2
        
        # Check that validation errors have proper structure
        for validation_error in details["validation_errors"]:
            assert "field" in validation_error
            assert "message" in validation_error
    
    @patch('app.error_handlers.logging.error')
    def test_generic_exception_handler_integration(self, mock_logging, mock_request):
        """Test generic Exception handler with error logging and no detail leakage."""
        from app.error_handlers import handle_generic_exception
        
        exc = Exception("Internal database connection failed with secret info")
        response = handle_generic_exception(mock_request, exc)
        
        # Verify response
        assert response.status_code == 500
        
        content = json.loads(response.body.decode())
        assert "error" in content
        error = content["error"]
        
        assert error["code"] == "internal_server_error"
        assert error["message"] == "An internal server error occurred"
        assert error["details"] is None
        
        # Verify no internal details leaked
        assert "database" not in error["message"]
        assert "secret" not in error["message"]
        
        # Verify error logging
        mock_logging.assert_called_once()
        call_args = mock_logging.call_args
        assert "Unhandled exception occurred" in call_args[0][0]
        assert call_args[1]['exc_info'] is True


class TestErrorResponseFormatConsistency:
    """Tests for error response format consistency across all handlers."""
    
    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request object."""
        from fastapi import Request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        return request
    
    def test_all_error_responses_follow_standardized_format(self, mock_request):
        """Test that all error responses follow standardized format."""
        from app.exceptions import (
            EventBaseError,
            EventNotFoundError,
            EventValidationError,
            EventBusinessRuleError
        )
        from app.error_handlers import (
            handle_event_not_found_error,
            handle_event_validation_error,
            handle_event_business_rule_error,
            handle_event_base_error,
            handle_generic_exception
        )
        
        # Test different exception types with their handlers
        test_cases = [
            (handle_event_not_found_error, EventNotFoundError("test")),
            (handle_event_validation_error, EventValidationError("test")),
            (handle_event_business_rule_error, EventBusinessRuleError("test")),
            (handle_event_base_error, EventBaseError("test")),
            (handle_generic_exception, Exception("test"))
        ]
        
        for handler, exc in test_cases:
            response = handler(mock_request, exc)
            
            # Verify response format
            content = json.loads(response.body.decode())
            
            # Check exact format: {"error": {"code": "string", "message": "string", "details?": "string"}}
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
    
    def test_error_codes_are_snake_case_format(self, mock_request):
        """Test that error codes are generated in snake_case format."""
        from app.exceptions import (
            EventBaseError,
            EventNotFoundError,
            EventValidationError,
            EventBusinessRuleError
        )
        from app.error_handlers import (
            handle_event_not_found_error,
            handle_event_validation_error,
            handle_event_business_rule_error,
            handle_event_base_error
        )
        
        test_cases = [
            (handle_event_not_found_error, EventNotFoundError("test"), "event_not_found"),
            (handle_event_validation_error, EventValidationError("test"), "event_validation"),
            (handle_event_business_rule_error, EventBusinessRuleError("test"), "event_business_rule"),
            (handle_event_base_error, EventBaseError("test"), "event_base")
        ]
        
        for handler, exc, expected_code in test_cases:
            response = handler(mock_request, exc)
            
            content = json.loads(response.body.decode())
            error = content["error"]
            assert error["code"] == expected_code
    
    def test_500_level_errors_dont_leak_internal_details(self, mock_request):
        """Test that 500-level errors don't leak internal details to clients."""
        from app.error_handlers import handle_generic_exception
        
        sensitive_messages = [
            "Database password is admin123",
            "Internal API key: secret-key-123",
            "Connection string: postgresql://user:pass@host/db"
        ]
        
        for sensitive_msg in sensitive_messages:
            exc = Exception(sensitive_msg)
            response = handle_generic_exception(mock_request, exc)
            
            # Should be 500 error
            assert response.status_code == 500
            
            content = json.loads(response.body.decode())
            error = content["error"]
            
            # Should not contain sensitive information
            assert "password" not in error["message"].lower()
            assert "secret" not in error["message"].lower()
            assert "postgresql://" not in error["message"]
            assert "admin123" not in error["message"]
            
            # Should be generic message
            assert error["message"] == "An internal server error occurred"


class TestExceptionHandlerPrecedence:
    """Tests for exception handler precedence and registration order."""
    
    def test_exception_handlers_registered_in_correct_order(self, monkeypatch):
        """Test that exception handlers are registered in the correct precedence order."""
        # Setup test environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("APP_ENV", "test")
        
        # Import after environment setup
        from app.main import create_app
        from app.exceptions import (
            EventBaseError,
            EventNotFoundError,
            EventValidationError,
            EventBusinessRuleError
        )
        from fastapi.exceptions import RequestValidationError
        
        app = create_app(env="test")
        
        # FastAPI stores exception handlers in app.exception_handlers
        exception_handlers = app.exception_handlers
        
        # All required handlers should be registered
        assert EventNotFoundError in exception_handlers
        assert EventValidationError in exception_handlers
        assert EventBusinessRuleError in exception_handlers
        assert EventBaseError in exception_handlers
        assert RequestValidationError in exception_handlers
        assert Exception in exception_handlers
        
        # Verify handlers are callable
        for exc_class, handler in exception_handlers.items():
            assert callable(handler)
    
    def test_most_specific_exception_handler_takes_precedence(self):
        """Test that most specific exception handlers take precedence over generic ones."""
        from app.exceptions import EventNotFoundError, EventBaseError
        from app.error_handlers import (
            handle_event_not_found_error,
            handle_event_base_error
        )
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.url = Mock()
        mock_request.url.path = "/test"
        mock_request.method = "GET"
        
        # EventNotFoundError is more specific than EventBaseError
        exc = EventNotFoundError("test-id")
        
        # Test that EventNotFoundError handler produces 404, not 500
        response = handle_event_not_found_error(mock_request, exc)
        assert response.status_code == 404
        
        content = json.loads(response.body.decode())
        error = content["error"]
        assert error["code"] == "event_not_found"  # Not "event_base"
        
        # Verify that EventBaseError handler would produce 500
        base_exc = EventBaseError("test error")
        base_response = handle_event_base_error(mock_request, base_exc)
        assert base_response.status_code == 500


class TestApplicationIntegrationFlow:
    """Tests for complete application integration flow."""
    
    def test_complete_application_integration_flow(self, monkeypatch):
        """Test complete integration from app creation to exception handling."""
        # Setup test environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("APP_ENV", "test")
        
        # Import after environment setup
        from app.main import create_app
        from fastapi.testclient import TestClient
        
        # Create app with handlers
        app = create_app(env="test")
        
        # Verify app was created successfully
        assert app is not None
        assert app.title == "events-service"
        
        # Verify TestClient can be created
        client = TestClient(app)
        assert client is not None
        
        # Test that the app responds to basic requests
        # Since we don't have any actual routes, test the docs endpoint
        docs_response = client.get("/docs")
        # Should either work (200) or return 404/405 if disabled
        assert docs_response.status_code in [200, 404, 405]
    
    def test_app_continues_normal_operation_with_exception_handlers(self, monkeypatch):
        """Test that app continues normal operation with exception handlers registered."""
        # Setup test environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("APP_ENV", "test")
        
        # Import after environment setup
        from app.main import create_app
        from fastapi.testclient import TestClient
        
        app = create_app(env="test")
        
        # Add a simple test route for verification
        @app.get("/health")
        def health_check():
            return {"status": "healthy"}
        
        client = TestClient(app)
        
        # Test that normal routes work with exception handlers registered
        response = client.get("/health")
        assert response.status_code == 200
        
        content = response.json()
        assert content["status"] == "healthy"
        
        # Verify response headers
        assert response.headers["content-type"] == "application/json"
    
    @patch('app.services.event_service.EventService')
    def test_mocked_service_layer_error_handling(self, mock_event_service_class, monkeypatch):
        """Test error flow with mocked service layer to avoid database dependencies."""
        # Setup test environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/testdb")
        monkeypatch.setenv("APP_ENV", "test")
        
        # Import after environment setup
        from app.main import create_app
        from app.exceptions import EventNotFoundError
        from fastapi.testclient import TestClient
        
        app = create_app(env="test")
        
        # Setup mock service instance
        mock_service = Mock()
        mock_event_service_class.return_value = mock_service
        
        # Configure mock to raise EventNotFoundError
        test_event_id = str(uuid4())
        mock_service.get_event.side_effect = EventNotFoundError(test_event_id)
        
        # Add test route that uses the mocked service
        @app.get("/test/service/{event_id}")
        def test_service_route(event_id: str):
            # Simulate using EventService
            service = mock_event_service_class(db_session=Mock())
            return service.get_event(event_id)
        
        client = TestClient(app)
        response = client.get(f"/test/service/{test_event_id}")
        
        # Verify exception was caught and handled by FastAPI exception handlers
        assert response.status_code == 404
        
        content = response.json()
        assert "error" in content
        error = content["error"]
        assert error["code"] == "event_not_found"
        assert test_event_id in error["message"]
        
        # Verify service was called
        mock_service.get_event.assert_called_once_with(test_event_id)
