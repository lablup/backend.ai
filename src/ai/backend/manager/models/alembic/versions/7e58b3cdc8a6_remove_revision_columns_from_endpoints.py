"""remove resource_group column from endpoints table

Revision ID: 7e58b3cdc8a6
Revises: e3111d960208
Create Date: 2026-03-31

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7e58b3cdc8a6"
down_revision = "e3111d960208"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The other revision-related columns (image, model, resource_slots, etc.)
    # were already removed in migration 8d01fe40664a.
    # This migration only removes the remaining resource_group column.

    # Remove foreign key constraint
    op.execute(
        "ALTER TABLE endpoints DROP CONSTRAINT IF EXISTS fk_endpoints_resource_group_scaling_groups"
    )

    # Remove index on resource_group
    op.execute("DROP INDEX IF EXISTS ix_endpoints_resource_group")

    # Remove resource_group column
    op.execute("ALTER TABLE endpoints DROP COLUMN IF EXISTS resource_group")


def downgrade() -> None:
    op.add_column("endpoints", sa.Column("resource_group", sa.String(), nullable=True))

    # Repopulate resource_group from deployment_revisions
    op.execute("""
        UPDATE endpoints e
        SET resource_group = dr.resource_group
        FROM deployment_revisions dr
        WHERE e.current_revision = dr.id
    """)

    # Re-create foreign key constraint
    op.create_foreign_key(
        "fk_endpoints_resource_group_scaling_groups",
        "endpoints",
        "scaling_groups",
        ["resource_group"],
        ["name"],
        ondelete="RESTRICT",
    )

    # Re-create index
    op.create_index("ix_endpoints_resource_group", "endpoints", ["resource_group"])
