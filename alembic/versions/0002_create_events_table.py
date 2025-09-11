from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "0002_create_events_table"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the events table
    op.create_table(
        "events",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("start_datetime", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("(end_datetime IS NULL OR end_datetime > start_datetime)", name="end_after_start"),
    )

    # Create index on start_datetime
    op.create_index(
        "ix_events_start_datetime",
        "events",
        ["start_datetime"],
        unique=False,
    )


def downgrade() -> None:
    # Drop index explicitly then the table
    op.drop_index("ix_events_start_datetime", table_name="events")
    op.drop_table("events")
