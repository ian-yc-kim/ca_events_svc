"""Exception handlers for FastAPI application error handling."""

import json
import logging
import re
from typing import List, Dict, Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions import (
    EventBaseError,
    EventNotFoundError,
    EventValidationError,
    EventBusinessRuleError
)
from app.schemas.error import ErrorResponse, ErrorDetail


def generate_error_code(exception_class_name: str) -> str:
    """Convert exception class name to snake_case error code.
    
    Args:
        exception_class_name: The exception class name to convert
        
    Returns:
        snake_case error code string
        
    Examples:
        EventNotFoundError -> event_not_found
        RequestValidationError -> validation_error
        Exception -> internal_server_error
    """
    # Special cases
    if exception_class_name == "RequestValidationError":
        return "validation_error"
    if exception_class_name == "Exception":
        return "internal_server_error"
    
    # Remove 'Error' suffix
    name = exception_class_name
    if name.endswith('Error'):
        name = name[:-5]
    
    # Convert CamelCase to snake_case
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def _get_exception_message(exc: Exception) -> str:
    """Safely extract message from exception with fallback.
    
    Args:
        exc: Exception instance
        
    Returns:
        Exception message or default fallback
    """
    # Try various ways to get a meaningful message
    if hasattr(exc, 'message') and exc.message:
        return str(exc.message)
    elif str(exc).strip():
        return str(exc)
    else:
        return f"An error occurred: {exc.__class__.__name__}"


def _format_validation_errors(validation_errors: List[Dict[str, Any]]) -> str:
    """Format Pydantic validation errors as structured JSON string.
    
    Args:
        validation_errors: List of validation error dictionaries from Pydantic
        
    Returns:
        JSON string with structured validation error details
    """
    error_details = []
    
    for error in validation_errors:
        # Extract field path (join location list with dots)
        field_path = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        
        error_details.append({
            "field": field_path,
            "message": message
        })
    
    return json.dumps({"validation_errors": error_details})


def handle_event_not_found_error(request: Request, exc: EventNotFoundError) -> JSONResponse:
    """Handle EventNotFoundError exceptions.
    
    Args:
        request: FastAPI request object
        exc: EventNotFoundError instance
        
    Returns:
        JSONResponse with 404 status and ErrorResponse format
    """
    error_code = generate_error_code(exc.__class__.__name__)
    error_response = ErrorResponse(
        code=error_code,
        message=_get_exception_message(exc)
    )
    
    return JSONResponse(
        status_code=404,
        content={"error": error_response.model_dump()}
    )


def handle_event_validation_error(request: Request, exc: EventValidationError) -> JSONResponse:
    """Handle EventValidationError exceptions.
    
    Args:
        request: FastAPI request object
        exc: EventValidationError instance
        
    Returns:
        JSONResponse with 400 status and ErrorResponse format
    """
    error_code = generate_error_code(exc.__class__.__name__)
    error_response = ErrorResponse(
        code=error_code,
        message=_get_exception_message(exc)
    )
    
    return JSONResponse(
        status_code=400,
        content={"error": error_response.model_dump()}
    )


def handle_event_business_rule_error(request: Request, exc: EventBusinessRuleError) -> JSONResponse:
    """Handle EventBusinessRuleError exceptions.
    
    Args:
        request: FastAPI request object
        exc: EventBusinessRuleError instance
        
    Returns:
        JSONResponse with 400 status and ErrorResponse format (per task requirements)
    """
    error_code = generate_error_code(exc.__class__.__name__)
    error_response = ErrorResponse(
        code=error_code,
        message=_get_exception_message(exc)
    )
    
    return JSONResponse(
        status_code=400,
        content={"error": error_response.model_dump()}
    )


def handle_event_base_error(request: Request, exc: EventBaseError) -> JSONResponse:
    """Handle EventBaseError exceptions (fallback for unhandled event errors).
    
    Args:
        request: FastAPI request object
        exc: EventBaseError instance
        
    Returns:
        JSONResponse with 500 status and ErrorResponse format
    """
    # Log 500-level errors for debugging
    logging.error(f"EventBaseError occurred: {exc}", exc_info=True)
    
    error_code = generate_error_code(exc.__class__.__name__)
    error_response = ErrorResponse(
        code=error_code,
        message=_get_exception_message(exc)
    )
    
    return JSONResponse(
        status_code=500,
        content={"error": error_response.model_dump()}
    )


def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI RequestValidationError exceptions.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse with 400 status and ErrorResponse format with structured details
    """
    error_code = generate_error_code(exc.__class__.__name__)
    
    # Format validation errors as structured JSON
    validation_details = _format_validation_errors(exc.errors())
    
    error_response = ErrorResponse(
        code=error_code,
        message="Request validation failed",
        details=validation_details
    )
    
    return JSONResponse(
        status_code=400,
        content={"error": error_response.model_dump()}
    )


def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic Exception instances (fallback handler).
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSONResponse with 500 status and generic ErrorResponse (no internal details)
    """
    # Log 500-level errors for debugging
    logging.error(f"Unhandled exception occurred: {exc}", exc_info=True)
    
    error_code = generate_error_code(exc.__class__.__name__)
    
    # Generic message to avoid leaking internal details
    error_response = ErrorResponse(
        code=error_code,
        message="An internal server error occurred"
    )
    
    return JSONResponse(
        status_code=500,
        content={"error": error_response.model_dump()}
    )
