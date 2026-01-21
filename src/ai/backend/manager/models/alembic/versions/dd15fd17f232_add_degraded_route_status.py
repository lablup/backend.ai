"""add_degraded_route_status

Revision ID: dd15fd17f232
Revises: 4cfe35b1e60a
Create Date: 2025-11-20 15:13:46.120822

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "dd15fd17f232"
down_revision = "4cfe35b1e60a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'degraded' value to routestatus enum
    op.execute("ALTER TYPE routestatus ADD VALUE IF NOT EXISTS 'degraded'")


def downgrade() -> None:
    # Note: PostgreSQL does not support removing enum values
    # Manual intervention required if downgrade is needed
    pass
