"""adopt lifecycle timestamps mixin on keypairs and user_profiles

Renames the legacy ``modified_at`` columns of keypairs / user_profiles to
``updated_at``, backfills NULLs and sets both timestamps NOT NULL so the
mixin's declaration holds.

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

_RENAMED_TABLES = ("keypairs", "user_profiles")

# (table, column, backfill expression) — created_at is backfilled from the
# sibling timestamp first, so the sibling's own backfill sees a non-NULL value.
_TARGETS = (
    ("keypairs", "created_at", "COALESCE(updated_at, now())"),
    ("keypairs", "updated_at", "COALESCE(created_at, now())"),
    ("user_profiles", "created_at", "COALESCE(updated_at, now())"),
    ("user_profiles", "updated_at", "COALESCE(created_at, now())"),
)


def upgrade() -> None:
    for table in _RENAMED_TABLES:
        op.alter_column(table, "modified_at", new_column_name="updated_at")
    for table, column, backfill in _TARGETS:
        op.execute(sa.text(f"UPDATE {table} SET {column} = {backfill} WHERE {column} IS NULL"))
        op.alter_column(table, column, nullable=False)


def downgrade() -> None:
    for table, column, _ in reversed(_TARGETS):
        op.alter_column(table, column, nullable=True)
    for table in reversed(_RENAMED_TABLES):
        op.alter_column(table, "updated_at", new_column_name="modified_at")
