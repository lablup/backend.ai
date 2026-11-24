"""Add resource_group_id to kernel_groups.

NULL means the session's resource group, which holds for every existing row.

Revision ID: 5b0d7e3f9a26
Revises: e7eaefa0781a
Create Date: 2026-11-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5b0d7e3f9a26"
down_revision = "e7eaefa0781a"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("kernel_groups", sa.Column("resource_group_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_kernel_groups_resource_group_id_scaling_groups"),
        "kernel_groups",
        "scaling_groups",
        ["resource_group_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_kernel_groups_resource_group_id"), "kernel_groups", ["resource_group_id"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_kernel_groups_resource_group_id"), table_name="kernel_groups")
    op.drop_constraint(
        op.f("fk_kernel_groups_resource_group_id_scaling_groups"),
        "kernel_groups",
        type_="foreignkey",
    )
    op.drop_column("kernel_groups", "resource_group_id")
