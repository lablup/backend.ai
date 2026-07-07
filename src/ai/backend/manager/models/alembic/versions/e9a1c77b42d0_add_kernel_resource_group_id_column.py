"""add kernel resource_group_id column

Add ``kernels.resource_group_id`` (UUID FK to ``scaling_groups.id``)
alongside the legacy ``kernels.scaling_group`` name column, following
the session-row pattern (BA-6644), so kernel data becomes
id-addressable before reader migration and the PK swap (BA-6050).

A kernel always belongs to a resource group (the same invariant
``b4c5d6e7f8a9`` established for sessions), so both columns become
NOT NULL: kernels whose ``scaling_group`` is NULL predate that
invariant and are unschedulable leftovers — they are deleted here
(dependent ``resource_allocations`` / ``vfolder_attachment`` rows
cascade).

Revision ID: e9a1c77b42d0
Revises: 66d0f891ed20
Create Date: 2026-07-06

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "e9a1c77b42d0"
down_revision = "66d0f891ed20"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("DELETE FROM kernels WHERE scaling_group IS NULL"))
    op.alter_column("kernels", "scaling_group", existing_type=sa.String(length=64), nullable=False)

    op.add_column("kernels", sa.Column("resource_group_id", GUID(), nullable=True))

    # The scaling_group name FK guarantees every remaining row matches a
    # scaling_groups row, so the backfill leaves no NULLs behind. The index
    # is created after the backfill so the bulk UPDATE does not pay index
    # maintenance per row.
    op.execute(
        sa.text("""
        UPDATE kernels
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE kernels.scaling_group = scaling_groups.name
          AND kernels.resource_group_id IS NULL
        """)
    )
    op.alter_column("kernels", "resource_group_id", nullable=False)
    op.create_index("ix_kernels_resource_group_id", "kernels", ["resource_group_id"])
    op.create_foreign_key(
        op.f("fk_kernels_resource_group_id_scaling_groups"),
        "kernels",
        "scaling_groups",
        ["resource_group_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_kernels_resource_group_id_scaling_groups"),
        "kernels",
        type_="foreignkey",
    )
    op.drop_index("ix_kernels_resource_group_id", table_name="kernels")
    op.drop_column("kernels", "resource_group_id")
    op.alter_column("kernels", "scaling_group", existing_type=sa.String(length=64), nullable=True)
