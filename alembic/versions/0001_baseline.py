from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Baseline: no-op
    pass

def downgrade() -> None:
    # Baseline: no-op
    pass
