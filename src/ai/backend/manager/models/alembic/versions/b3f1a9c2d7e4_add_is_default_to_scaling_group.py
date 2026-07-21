"""add is_default to scaling_group

Revision ID: b3f1a9c2d7e4
Revises: aa27f1d5cd35
Create Date: 2026-07-15 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b3f1a9c2d7e4"
down_revision = "aa27f1d5cd35"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    # is_default marks the single default scaling group. The partial unique index
    # guarantees at most one row has is_default = true (a minimum of one is NOT
    # guaranteed). Both statements use IF NOT EXISTS so the migration is idempotent
    # and safe to re-apply (including on backport).
    op.execute(
        "ALTER TABLE scaling_groups "
        "ADD COLUMN IF NOT EXISTS is_default boolean NOT NULL DEFAULT false"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_scaling_groups_is_default "
        "ON scaling_groups (is_default) WHERE is_default"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_scaling_groups_is_default")
    op.execute("ALTER TABLE scaling_groups DROP COLUMN IF EXISTS is_default")
