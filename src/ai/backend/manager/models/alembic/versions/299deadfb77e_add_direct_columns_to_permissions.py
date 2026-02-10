"""add direct columns to permissions

Revision ID: 299deadfb77e
Revises: 8fd6f47bd226
Create Date: 2026-02-10 21:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "299deadfb77e"
down_revision = "8fd6f47bd226"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add columns (nullable initially)
    op.add_column("permissions", sa.Column("role_id", GUID(), nullable=True))
    op.add_column("permissions", sa.Column("scope_type", sa.String(32), nullable=True))
    op.add_column("permissions", sa.Column("scope_id", sa.String(64), nullable=True))

    # 2. Backfill from permission_groups
    op.execute(
        """
        UPDATE permissions p
        SET role_id = pg.role_id,
            scope_type = pg.scope_type,
            scope_id = pg.scope_id
        FROM permission_groups pg
        WHERE p.permission_group_id = pg.id
        """
    )

    # 3. ALTER columns to NOT NULL
    op.alter_column("permissions", "role_id", nullable=False)
    op.alter_column("permissions", "scope_type", nullable=False)
    op.alter_column("permissions", "scope_id", nullable=False)

    # 4. Add composite index
    op.create_index(
        "ix_permissions_role_scope", "permissions", ["role_id", "scope_type", "scope_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_permissions_role_scope", table_name="permissions")
    op.drop_column("permissions", "scope_id")
    op.drop_column("permissions", "scope_type")
    op.drop_column("permissions", "role_id")
