"""rename domains.modified_at to updated_at

``domains`` kept a hand-rolled ``modified_at`` while the tables renamed in
``2dccb3069031`` moved onto ``LifecycleTimestampsMixin``'s ``updated_at``.
Renames the column and, since neither timestamp was ever tightened, backfills
the NULLs and sets both NOT NULL as the mixin declares them.

Revision ID: c4d1a7e58b32
Revises: b9e3a7c14f28
Create Date: 2026-08-13 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4d1a7e58b32"
down_revision = "b9e3a7c14f28"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("domains", "modified_at", new_column_name="updated_at")
    # created_at is backfilled first, so a row with both timestamps NULL leaves
    # this statement with now() for the updated_at backfill to read.
    op.execute(
        sa.text(
            "UPDATE domains SET created_at = COALESCE(updated_at, now()) WHERE created_at IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE domains SET updated_at = COALESCE(created_at, now()) WHERE updated_at IS NULL"
        )
    )
    op.alter_column("domains", "created_at", nullable=False)
    op.alter_column("domains", "updated_at", nullable=False)


def downgrade() -> None:
    op.alter_column("domains", "updated_at", nullable=True)
    op.alter_column("domains", "created_at", nullable=True)
    op.alter_column("domains", "updated_at", new_column_name="modified_at")
