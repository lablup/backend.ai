"""adopt lifecycle timestamps mixin on keypairs

Renames the legacy ``modified_at`` column of keypairs to ``updated_at``,
backfills NULLs and sets both timestamps NOT NULL so the mixin's declaration
holds.

Revision ID: ebe5354693b3
Revises: 1449797cc931
Create Date: 2026-08-13 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ebe5354693b3"
down_revision: str | None = "1449797cc931"
# Part of: NEXT_RELEASE_VERSION
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (column, backfill expression) — created_at is backfilled from the sibling
# timestamp first, so the sibling's own backfill sees a non-NULL value.
_TARGETS = (
    ("created_at", "COALESCE(updated_at, now())"),
    ("updated_at", "COALESCE(created_at, now())"),
)


def upgrade() -> None:
    op.alter_column("keypairs", "modified_at", new_column_name="updated_at")
    for column, backfill in _TARGETS:
        op.execute(sa.text(f"UPDATE keypairs SET {column} = {backfill} WHERE {column} IS NULL"))
        op.alter_column("keypairs", column, nullable=False)


def downgrade() -> None:
    for column, _ in reversed(_TARGETS):
        op.alter_column("keypairs", column, nullable=True)
    op.alter_column("keypairs", "updated_at", new_column_name="modified_at")
