"""Add the kernel group tables and the kernel's group foreign key.

A kernel group is one role of a session. Existing rows are not backfilled here:
``kernels.kernel_group_id`` stays NULL on them and nullable until the enqueue
write sets it on new rows.

Revision ID: c9e1b7a4d2f0
Revises: fa2dfd48c169
Create Date: 2026-10-20

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9e1b7a4d2f0"
down_revision = "fa2dfd48c169"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

ENVIRON_KEY_PATTERN = "^[A-Za-z_][A-Za-z0-9_]*$"


def upgrade() -> None:
    op.create_table(
        "kernel_groups",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("image_id", sa.Uuid(), nullable=True),
        sa.Column("shmem", sa.BigInteger(), nullable=True),
        sa.Column("startup_command", sa.Text(), nullable=True),
        sa.Column(
            "preopen_ports",
            sa.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("requested_starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("batch_timeout_sec", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kernel_groups")),
        sa.UniqueConstraint("session_id", "role", name=op.f("uq_kernel_groups_session_id")),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_kernel_groups_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["images.id"],
            name=op.f("fk_kernel_groups_image_id_images"),
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_kernel_groups_image_id", "kernel_groups", ["image_id"])

    op.create_table(
        "kernel_group_resource_slots",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("kernel_group_id", sa.Uuid(), nullable=False),
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kernel_group_resource_slots")),
        sa.UniqueConstraint(
            "kernel_group_id",
            "slot_name",
            name=op.f("uq_kernel_group_resource_slots_kernel_group_id"),
        ),
        sa.ForeignKeyConstraint(
            ["kernel_group_id"],
            ["kernel_groups.id"],
            name=op.f("fk_kernel_group_resource_slots_kernel_group_id_kernel_groups"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name=op.f("fk_kernel_group_resource_slots_slot_name_resource_slot_types"),
        ),
    )
    op.create_index(
        "ix_kernel_group_resource_slots_slot_name", "kernel_group_resource_slots", ["slot_name"]
    )

    op.create_table(
        "kernel_group_environ",
        sa.Column("kernel_group_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=256), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("kernel_group_id", "key", name=op.f("pk_kernel_group_environ")),
        sa.CheckConstraint(
            f"key ~ '{ENVIRON_KEY_PATTERN}'",
            name=op.f("ck_kernel_group_environ_key_is_environ_name"),
        ),
        sa.ForeignKeyConstraint(
            ["kernel_group_id"],
            ["kernel_groups.id"],
            name=op.f("fk_kernel_group_environ_kernel_group_id_kernel_groups"),
            ondelete="CASCADE",
        ),
    )

    op.add_column("kernels", sa.Column("kernel_group_id", sa.Uuid(), nullable=True))
    op.create_index("ix_kernels_kernel_group_id", "kernels", ["kernel_group_id"])
    op.create_foreign_key(
        "fk_kernels_kernel_group_id_kernel_groups",
        "kernels",
        "kernel_groups",
        ["kernel_group_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_kernels_kernel_group_id_kernel_groups",
        "kernels",
        type_="foreignkey",
    )
    op.drop_index("ix_kernels_kernel_group_id", table_name="kernels")
    op.drop_column("kernels", "kernel_group_id")
    op.drop_index(
        "ix_kernel_group_resource_slots_slot_name", table_name="kernel_group_resource_slots"
    )
    op.drop_table("kernel_group_environ")
    op.drop_table("kernel_group_resource_slots")
    op.drop_index("ix_kernel_groups_image_id", table_name="kernel_groups")
    op.drop_table("kernel_groups")
