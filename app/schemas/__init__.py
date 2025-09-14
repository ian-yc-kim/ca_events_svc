"""Pydantic schemas for API request/response models."""

from .event import EventCreateSchema, EventUpdateSchema, EventResponseSchema
from .error import ErrorResponse, ErrorDetail

__all__ = [
    "EventCreateSchema", 
    "EventUpdateSchema", 
    "EventResponseSchema",
    "ErrorResponse",
    "ErrorDetail"
]
