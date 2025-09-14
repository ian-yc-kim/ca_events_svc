"""Event service layer with business rule validation and dependency injection."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import (
    EventNotFoundError,
    EventValidationError,
    EventBusinessRuleError,
)
from app.models.event import Event
from app.schemas.event import EventCreateSchema, EventUpdateSchema


class EventService:
    """Service class for event operations with business rule validation."""
    
    def __init__(self, db_session: Session) -> None:
        """Initialize EventService with database session dependency.
        
        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db_session = db_session
        self.settings = get_settings()
    
    def create_event(self, event_data: EventCreateSchema) -> Event:
        """Create a new event with business rule validation.
        
        Args:
            event_data: Validated event creation data
            
        Returns:
            Event: Created event object
            
        Raises:
            EventBusinessRuleError: If business rules are violated
            EventValidationError: If database constraints are violated
        """
        try:
            # Convert schema to dict for validation
            event_dict = event_data.model_dump()
            
            # Validate business rules
            self._validate_business_rules(event_dict)
            
            # Create event model instance
            event = Event(**event_dict)
            
            # Persist to database
            self.db_session.add(event)
            self.db_session.commit()
            self.db_session.refresh(event)
            
            logging.info(f"Event created successfully with ID: {event.id}")
            return event
            
        except IntegrityError as e:
            logging.error(f"Database integrity error during event creation: {e}", exc_info=True)
            self.db_session.rollback()
            raise EventValidationError(
                "Event creation failed due to data validation constraints"
            ) from e
        except SQLAlchemyError as e:
            logging.error(f"Database error during event creation: {e}", exc_info=True)
            self.db_session.rollback()
            raise EventValidationError(
                "Event creation failed due to database error"
            ) from e
        except Exception as e:
            logging.error(f"Unexpected error during event creation: {e}", exc_info=True)
            self.db_session.rollback()
            raise
    
    def get_event(self, event_id: UUID) -> Event:
        """Retrieve a single event by ID.
        
        Args:
            event_id: UUID of the event to retrieve
            
        Returns:
            Event: Retrieved event object
            
        Raises:
            EventNotFoundError: If event is not found
        """
        try:
            stmt = select(Event).where(Event.id == event_id)
            event = self.db_session.execute(stmt).scalar_one_or_none()
            
            if event is None:
                raise EventNotFoundError(str(event_id))
            
            logging.info(f"Event retrieved successfully with ID: {event_id}")
            return event
            
        except EventNotFoundError:
            # Re-raise business exceptions
            raise
        except SQLAlchemyError as e:
            logging.error(f"Database error during event retrieval: {e}", exc_info=True)
            raise EventValidationError(
                "Event retrieval failed due to database error"
            ) from e
        except Exception as e:
            logging.error(f"Unexpected error during event retrieval: {e}", exc_info=True)
            raise
    
    def update_event(self, event_id: UUID, update_data: EventUpdateSchema) -> Event:
        """Update an existing event with partial update support.
        
        Args:
            event_id: UUID of the event to update
            update_data: Validated update data (partial)
            
        Returns:
            Event: Updated event object
            
        Raises:
            EventNotFoundError: If event is not found
            EventBusinessRuleError: If business rules are violated
            EventValidationError: If database constraints are violated
        """
        try:
            # Retrieve existing event
            event = self.get_event(event_id)
            
            # Get update data excluding unset fields
            update_dict = update_data.model_dump(exclude_none=True)
            
            if not update_dict:
                # No fields to update
                logging.info(f"No fields to update for event ID: {event_id}")
                return event
            
            # Create combined data for business rule validation
            combined_data = {
                "start_datetime": event.start_datetime,
                "end_datetime": event.end_datetime,
                "title": event.title,
                "description": event.description,
            }
            combined_data.update(update_dict)
            
            # Validate business rules with combined data
            self._validate_business_rules(combined_data)
            
            # Apply updates
            for field, value in update_dict.items():
                setattr(event, field, value)
            
            # Persist changes
            self.db_session.commit()
            self.db_session.refresh(event)
            
            logging.info(f"Event updated successfully with ID: {event_id}")
            return event
            
        except (EventNotFoundError, EventBusinessRuleError):
            # Re-raise business exceptions
            raise
        except IntegrityError as e:
            logging.error(f"Database integrity error during event update: {e}", exc_info=True)
            self.db_session.rollback()
            raise EventValidationError(
                "Event update failed due to data validation constraints"
            ) from e
        except SQLAlchemyError as e:
            logging.error(f"Database error during event update: {e}", exc_info=True)
            self.db_session.rollback()
            raise EventValidationError(
                "Event update failed due to database error"
            ) from e
        except Exception as e:
            logging.error(f"Unexpected error during event update: {e}", exc_info=True)
            self.db_session.rollback()
            raise
    
    def list_events(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Event]:
        """List events with pagination support.
        
        Args:
            limit: Maximum number of events to return (uses config default if None)
            offset: Number of events to skip
            
        Returns:
            List[Event]: List of events ordered by start_datetime
            
        Raises:
            EventValidationError: If database errors occur
        """
        try:
            # Apply default limit from configuration
            if limit is None:
                limit = self.settings.pagination_default_limit
            else:
                # Ensure limit doesn't exceed maximum
                limit = min(limit, self.settings.pagination_max_limit)
            
            # Build query with ordering and pagination
            stmt = (
                select(Event)
                .order_by(Event.start_datetime.asc())
                .offset(offset)
                .limit(limit)
            )
            
            result = self.db_session.execute(stmt)
            events = result.scalars().all()
            
            logging.info(f"Retrieved {len(events)} events with offset={offset}, limit={limit}")
            return list(events)
            
        except SQLAlchemyError as e:
            logging.error(f"Database error during event listing: {e}", exc_info=True)
            raise EventValidationError(
                "Event listing failed due to database error"
            ) from e
        except Exception as e:
            logging.error(f"Unexpected error during event listing: {e}", exc_info=True)
            raise
    
    def delete_event(self, event_id: UUID) -> bool:
        """Delete an event by ID.
        
        Args:
            event_id: UUID of the event to delete
            
        Returns:
            bool: True if deletion was successful
            
        Raises:
            EventNotFoundError: If event is not found
            EventValidationError: If database constraints prevent deletion
        """
        try:
            # Retrieve event to ensure it exists
            event = self.get_event(event_id)
            
            # Delete event
            self.db_session.delete(event)
            self.db_session.commit()
            
            logging.info(f"Event deleted successfully with ID: {event_id}")
            return True
            
        except EventNotFoundError:
            # Re-raise business exceptions
            raise
        except IntegrityError as e:
            logging.error(f"Database integrity error during event deletion: {e}", exc_info=True)
            self.db_session.rollback()
            raise EventValidationError(
                "Event deletion failed due to database constraints (e.g., foreign key references)"
            ) from e
        except SQLAlchemyError as e:
            logging.error(f"Database error during event deletion: {e}", exc_info=True)
            self.db_session.rollback()
            raise EventValidationError(
                "Event deletion failed due to database error"
            ) from e
        except Exception as e:
            logging.error(f"Unexpected error during event deletion: {e}", exc_info=True)
            self.db_session.rollback()
            raise
    
    def _validate_business_rules(self, event_data: Dict[str, Any]) -> None:
        """Validate business rules for event data.
        
        Args:
            event_data: Dictionary containing event data to validate
            
        Raises:
            EventBusinessRuleError: If business rules are violated
        """
        start_dt = event_data.get("start_datetime")
        end_dt = event_data.get("end_datetime")
        
        # Validate end_datetime > start_datetime if both are provided
        if start_dt and end_dt and end_dt <= start_dt:
            raise EventBusinessRuleError(
                "End datetime must be after start datetime"
            )
        
        logging.debug("Business rule validation passed for event data")
