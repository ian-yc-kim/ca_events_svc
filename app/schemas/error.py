"""Pydantic schemas for error response models."""

from typing import Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Schema for individual field error details in validation errors."""
    
    field: str = Field(..., description="Field name that caused the error")
    message: str = Field(..., description="Error message for the field")


class ErrorResponse(BaseModel):
    """Schema for standardized error responses across all endpoints."""
    
    code: str = Field(..., description="Error code in snake_case format")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details (JSON string for validation errors)")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "code": "event_not_found",
                "message": "Event with ID 'abc-123' not found",
                "details": None
            }
        }
