"""Pydantic schemas for Event API request/response models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.datetime import ensure_utc_aware


class EventCreateSchema(BaseModel):
    """Schema for creating new events with strict validation."""
    
    title: str = Field(..., description="Event title (1-255 characters)")
    description: Optional[str] = Field(None, description="Event description (up to 2000 characters)")
    start_datetime: datetime = Field(..., description="Event start time (timezone-aware, converted to UTC)")
    end_datetime: Optional[datetime] = Field(None, description="Event end time (timezone-aware, converted to UTC)")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title length and content."""
        if not isinstance(v, str):
            raise ValueError("Title must be a string")
            
        # Strip whitespace for length validation
        stripped = v.strip()
        if len(stripped) < 1:
            raise ValueError("Title must be between 1 and 255 characters")
            
        if len(v) > 255:
            raise ValueError("Title must be between 1 and 255 characters")
            
        return v
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description length."""
        if v is None:
            return v
            
        if not isinstance(v, str):
            raise ValueError("Description must be a string")
            
        if len(v) > 2000:
            raise ValueError("Description cannot exceed 2000 characters")
            
        return v
    
    @field_validator("start_datetime", mode="before")
    @classmethod
    def validate_start_datetime(cls, v) -> datetime:
        """Validate and convert start_datetime to UTC."""
        return ensure_utc_aware(v)
    
    @field_validator("end_datetime", mode="before")
    @classmethod
    def validate_end_datetime(cls, v) -> Optional[datetime]:
        """Validate and convert end_datetime to UTC."""
        if v is None:
            return None
        return ensure_utc_aware(v)


class EventUpdateSchema(BaseModel):
    """Schema for updating existing events with optional fields."""
    
    title: Optional[str] = Field(None, description="Event title (1-255 characters)")
    description: Optional[str] = Field(None, description="Event description (up to 2000 characters)")
    start_datetime: Optional[datetime] = Field(None, description="Event start time (timezone-aware, converted to UTC)")
    end_datetime: Optional[datetime] = Field(None, description="Event end time (timezone-aware, converted to UTC)")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title length and content when provided."""
        if v is None:
            return v
            
        if not isinstance(v, str):
            raise ValueError("Title must be a string")
            
        # Strip whitespace for length validation
        stripped = v.strip()
        if len(stripped) < 1:
            raise ValueError("Title must be between 1 and 255 characters")
            
        if len(v) > 255:
            raise ValueError("Title must be between 1 and 255 characters")
            
        return v
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description length when provided."""
        if v is None:
            return v
            
        if not isinstance(v, str):
            raise ValueError("Description must be a string")
            
        if len(v) > 2000:
            raise ValueError("Description cannot exceed 2000 characters")
            
        return v
    
    @field_validator("start_datetime", mode="before")
    @classmethod
    def validate_start_datetime(cls, v) -> Optional[datetime]:
        """Validate and convert start_datetime to UTC when provided."""
        if v is None:
            return None
        return ensure_utc_aware(v)
    
    @field_validator("end_datetime", mode="before")
    @classmethod
    def validate_end_datetime(cls, v) -> Optional[datetime]:
        """Validate and convert end_datetime to UTC when provided."""
        if v is None:
            return None
        return ensure_utc_aware(v)


class EventResponseSchema(BaseModel):
    """Schema for Event API responses."""
    
    id: UUID = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_datetime: datetime = Field(..., description="Event start time (UTC)")
    end_datetime: Optional[datetime] = Field(None, description="Event end time (UTC)")
    created_at: datetime = Field(..., description="Event creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Event last update timestamp (UTC)")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True  # Enable ORM model conversion
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
