"""add session limit attributes to resource slot types

Revision ID: 5c02b1595f28
Revises: ede445fb9d0d
Create Date: 2026-10-13

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "5c02b1595f28"  # Part of: NEXT_RELEASE_VERSION
down_revision = "ede445fb9d0d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        ADD COLUMN IF NOT EXISTS sealed_launch BOOLEAN NOT NULL DEFAULT false,
        ADD COLUMN IF NOT EXISTS max_per_session NUMERIC(24, 6),
        ADD COLUMN IF NOT EXISTS single_node_only BOOLEAN NOT NULL DEFAULT false
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        DROP COLUMN IF EXISTS sealed_launch,
        DROP COLUMN IF EXISTS max_per_session,
        DROP COLUMN IF EXISTS single_node_only
        """
    )
