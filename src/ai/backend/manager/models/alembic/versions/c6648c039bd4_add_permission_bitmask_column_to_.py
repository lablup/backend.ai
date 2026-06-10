"""add permission bitmask column to permissions

Revision ID: c6648c039bd4
Revises: a3f1c7e2b9d4
Create Date: 2026-06-11 01:51:27.442017

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c6648c039bd4"
down_revision = "a3f1c7e2b9d4"
# Part of: 26.6.0
branch_labels = None
depends_on = None

# Bit values mirror ai.backend.common.data.permission.types.Permission (IntFlag).
# Grant operations (grant:*) have no dedicated bit and backfill to 0 (NONE);
# grant authority remains carried by the legacy `operation` column.
_BACKFILL_PERMISSION_FROM_OPERATION = sa.text("""
    UPDATE permissions SET permission = CASE operation
        WHEN 'read' THEN 1
        WHEN 'update' THEN 2
        WHEN 'create' THEN 4
        WHEN 'soft-delete' THEN 8
        WHEN 'hard-delete' THEN 16
        ELSE 0
    END
""")


def upgrade() -> None:
    op.add_column(
        "permissions",
        sa.Column("permission", sa.SmallInteger(), nullable=True),
    )
    op.execute(_BACKFILL_PERMISSION_FROM_OPERATION)
    op.alter_column("permissions", "permission", nullable=False)


def downgrade() -> None:
    op.drop_column("permissions", "permission")
