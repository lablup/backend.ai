"""add agent resource_group_id column

Add ``agents.resource_group_id`` (UUID FK to ``scaling_groups.id``)
alongside the legacy ``agents.scaling_group`` name column, following
the kernel-row pattern (``e9a1c77b42d0``), so agent data becomes
id-addressable before reader migration and the PK swap (BA-6050).

``agents.scaling_group`` is already NOT NULL with an FK to
``scaling_groups.name``, so the backfill leaves no NULLs behind and
the new column becomes NOT NULL directly.

Revision ID: 7f2b9c4d1a83
Revises: a560420476b6
Create Date: 2026-07-07

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "7f2b9c4d1a83"
down_revision = "a560420476b6"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("resource_group_id", GUID(), nullable=True))

    # The scaling_group name FK guarantees every row matches a scaling_groups
    # row, so the backfill leaves no NULLs behind. The index is created after
    # the backfill so the bulk UPDATE does not pay index maintenance per row.
    op.execute(
        sa.text("""
        UPDATE agents
        SET resource_group_id = scaling_groups.id
        FROM scaling_groups
        WHERE agents.scaling_group = scaling_groups.name
          AND agents.resource_group_id IS NULL
        """)
    )
    op.alter_column("agents", "resource_group_id", nullable=False)
    op.create_index("ix_agents_resource_group_id", "agents", ["resource_group_id"])
    op.create_foreign_key(
        op.f("fk_agents_resource_group_id_scaling_groups"),
        "agents",
        "scaling_groups",
        ["resource_group_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_agents_resource_group_id_scaling_groups"),
        "agents",
        type_="foreignkey",
    )
    op.drop_index("ix_agents_resource_group_id", table_name="agents")
    op.drop_column("agents", "resource_group_id")
