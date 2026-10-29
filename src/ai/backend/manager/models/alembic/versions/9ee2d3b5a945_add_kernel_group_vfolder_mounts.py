"""Add the kernel_group_vfolder_mounts table.

Existing kernels are not backfilled: their mounts stay in ``kernels.vfolder_mounts``.

Revision ID: 9ee2d3b5a945
Revises: 133c191ae872
Create Date: 2026-10-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9ee2d3b5a945"
down_revision = "133c191ae872"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kernel_group_vfolder_mounts",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("kernel_group_id", sa.Uuid(), nullable=False),
        sa.Column("vfolder_id", sa.Uuid(), nullable=False),
        sa.Column("vfsubpath", sa.Text(), nullable=False),
        sa.Column("mount_destination", sa.Text(), nullable=False),
        sa.Column("mount_perm", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kernel_group_vfolder_mounts")),
        sa.UniqueConstraint(
            "kernel_group_id",
            "mount_destination",
            name=op.f("uq_kernel_group_vfolder_mounts_kernel_group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["kernel_group_id"],
            ["kernel_groups.id"],
            name=op.f("fk_kernel_group_vfolder_mounts_kernel_group_id_kernel_groups"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["vfolder_id"],
            ["vfolders.id"],
            name="fk_kernel_group_vfolder_mounts_vfolder_id_vfolders",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_kernel_group_vfolder_mounts_vfolder_id",
        "kernel_group_vfolder_mounts",
        ["vfolder_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_kernel_group_vfolder_mounts_vfolder_id", table_name="kernel_group_vfolder_mounts"
    )
    op.drop_table("kernel_group_vfolder_mounts")
