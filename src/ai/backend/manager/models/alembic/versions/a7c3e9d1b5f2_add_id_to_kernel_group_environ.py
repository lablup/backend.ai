"""Add an id primary key to kernel_group_environ, keeping (kernel_group_id, key) unique.

Revision ID: a7c3e9d1b5f2
Revises: f73d1b0ee986
Create Date: 2026-10-26

"""

import sqlalchemy as sa
from alembic import op

revision = "a7c3e9d1b5f2"  # Part of: NEXT_RELEASE_VERSION
down_revision = "f73d1b0ee986"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "kernel_group_environ",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
    )
    op.drop_constraint("pk_kernel_group_environ", "kernel_group_environ", type_="primary")
    op.create_primary_key("pk_kernel_group_environ", "kernel_group_environ", ["id"])
    op.create_unique_constraint(
        "uq_kernel_group_environ_kernel_group_id",
        "kernel_group_environ",
        ["kernel_group_id", "key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_kernel_group_environ_kernel_group_id", "kernel_group_environ", type_="unique"
    )
    op.drop_constraint("pk_kernel_group_environ", "kernel_group_environ", type_="primary")
    op.create_primary_key(
        "pk_kernel_group_environ", "kernel_group_environ", ["kernel_group_id", "key"]
    )
    op.drop_column("kernel_group_environ", "id")
