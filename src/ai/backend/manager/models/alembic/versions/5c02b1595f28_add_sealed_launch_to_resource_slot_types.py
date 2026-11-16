"""add sealed_launch to resource slot types

Revision ID: 5c02b1595f28
Revises: 019493a701bd
Create Date: 2026-10-13

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "5c02b1595f28"
down_revision = "019493a701bd"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE resource_slot_types
        ADD COLUMN IF NOT EXISTS sealed_launch BOOLEAN NOT NULL DEFAULT false
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE resource_slot_types DROP COLUMN IF EXISTS sealed_launch")
