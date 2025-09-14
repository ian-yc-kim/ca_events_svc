"""DateTime utility functions for timezone handling and validation."""

from datetime import datetime, timezone
from typing import Any, Union
import logging


def ensure_utc_aware(value: Any) -> datetime:
    """Convert datetime input to UTC timezone-aware datetime.
    
    Accepts:
    - ISO 8601 strings with timezone info (including 'Z' suffix)
    - datetime objects with timezone info
    
    Rejects:
    - timezone-naive datetimes
    - invalid formats
    - None or empty values
    
    Args:
        value: Input value to convert to UTC-aware datetime
        
    Returns:
        datetime: UTC timezone-aware datetime object
        
    Raises:
        ValueError: If input is timezone-naive or invalid format
    """
    try:
        if value is None:
            raise ValueError("Datetime value cannot be None")
            
        # Handle string inputs (ISO 8601)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("Datetime string cannot be empty")
                
            # Handle 'Z' suffix (UTC indicator)
            if value.endswith('Z'):
                value = value[:-1] + '+00:00'
                
            # Parse ISO 8601 string
            try:
                dt = datetime.fromisoformat(value)
            except ValueError as e:
                raise ValueError(f"Invalid datetime format. Use ISO 8601 format with timezone. Error: {str(e)}")
                
        # Handle datetime objects
        elif isinstance(value, datetime):
            dt = value
        else:
            raise ValueError(f"Unsupported datetime type: {type(value)}. Expected string or datetime object")
            
        # Validate timezone awareness
        if dt.tzinfo is None:
            raise ValueError("Timezone-naive datetime not allowed. Please provide timezone information.")
            
        # Convert to UTC if not already
        if dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)
            
        return dt
        
    except ValueError:
        # Re-raise ValueError with original message
        raise
    except Exception as e:
        logging.error(f"Unexpected error in ensure_utc_aware: {e}", exc_info=True)
        raise ValueError(f"Failed to process datetime value: {str(e)}")
