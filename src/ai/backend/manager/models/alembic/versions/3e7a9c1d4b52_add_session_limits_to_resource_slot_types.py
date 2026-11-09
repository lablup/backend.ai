"""add session limit attributes to resource slot types

Revision ID: 3e7a9c1d4b52
Revises: 5c02b1595f28
Create Date: 2026-11-09

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "3e7a9c1d4b52"
down_revision = "5c02b1595f28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        ADD COLUMN IF NOT EXISTS max_per_session NUMERIC(24, 6),
        ADD COLUMN IF NOT EXISTS single_node_only BOOLEAN NOT NULL DEFAULT false
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        DROP COLUMN IF EXISTS max_per_session,
        DROP COLUMN IF EXISTS single_node_only
        """
    )
