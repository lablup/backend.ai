"""add enabled flag to resource slot types

Revision ID: bee1c0de01a1
Revises: 338bc3284f20
Create Date: 2026-05-27

"""

# Part of: 26.5.1

from alembic import op

# revision identifiers, used by Alembic.
revision = "bee1c0de01a1"
down_revision = "338bc3284f20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT true
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        DROP COLUMN IF EXISTS enabled
        """
    )
