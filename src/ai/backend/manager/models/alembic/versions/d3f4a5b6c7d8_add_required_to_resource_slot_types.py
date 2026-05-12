"""add required flag to resource slot types

Revision ID: d3f4a5b6c7d8
Revises: fc249eccd0b2
Create Date: 2026-05-12

"""

# Part of: 26.5.0

from alembic import op

# revision identifiers, used by Alembic.
revision = "d3f4a5b6c7d8"
down_revision = "fc249eccd0b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        ADD COLUMN IF NOT EXISTS required BOOLEAN NOT NULL DEFAULT false
        """
    )
    op.execute(
        """
        UPDATE resource_slot_types
        SET required = true
        WHERE slot_name IN ('cpu', 'mem')
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        DROP COLUMN IF EXISTS required
        """
    )
