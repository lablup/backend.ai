"""delete inactive login sessions

Revision ID: a3b7c9d1e5f2
Revises: 17b679c98b50
Create Date: 2026-04-13 22:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3b7c9d1e5f2"
down_revision = "ecc4b93d7907"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # LoginSession rows are now deleted on termination instead of status-updated.
    # Clean up all historical non-active rows; LoginHistory serves as the audit trail.
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM login_sessions WHERE status != 'active'"))


def downgrade() -> None:
    # Data-only cleanup: deleted rows cannot be restored.
    pass
