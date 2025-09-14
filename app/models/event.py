from __future__ import annotations

import uuid
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from app.db.base import Base


class Event(Base):
    __tablename__ = "events"
    
    id = sa.Column(pg.UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    title = sa.Column(sa.String(255), nullable=False)
    description = sa.Column(sa.String(2000), nullable=True)
    start_datetime = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, index=True)
    end_datetime = sa.Column(sa.TIMESTAMP(timezone=True), nullable=True)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    
    __table_args__ = (
        sa.CheckConstraint("(end_datetime IS NULL OR end_datetime > start_datetime)", name="end_after_start"),
    )
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', start_datetime='{self.start_datetime}')>"
