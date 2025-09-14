"""Custom exceptions for business logic and error handling."""


class EventBaseError(Exception):
    """Base exception for event-related errors."""
    
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class EventNotFoundError(EventBaseError):
    """Raised when an event is not found."""
    
    def __init__(self, event_id: str) -> None:
        message = f"Event with ID '{event_id}' not found"
        super().__init__(message)
        self.event_id = event_id


class EventValidationError(EventBaseError):
    """Raised for event validation failures."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message)


class EventBusinessRuleError(EventBaseError):
    """Raised for business rule violations."""
    
    def __init__(self, message: str) -> None:
        super().__init__(message)
