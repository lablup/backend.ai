"""add uid and gid columns

Revision ID: f6ca2f2d04c1
Revises: fb89f5d7817b
Create Date: 2024-12-20 12:16:07.077845

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f6ca2f2d04c1"
down_revision = "fb89f5d7817b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "kernels", sa.Column("uid", sa.Integer(), server_default=sa.text("NULL"), nullable=True)
    )
    op.add_column(
        "kernels",
        sa.Column("main_gid", sa.Integer(), server_default=sa.text("NULL"), nullable=True),
    )
    op.add_column(
        "kernels",
        sa.Column("gids", sa.ARRAY(sa.Integer()), server_default=sa.text("NULL"), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("container_uid", sa.Integer(), server_default=sa.text("NULL"), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "container_main_gid", sa.Integer(), server_default=sa.text("NULL"), nullable=True
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "container_gids",
            sa.ARRAY(sa.Integer()),
            server_default=sa.text("NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "container_main_gid")
    op.drop_column("users", "container_gids")
    op.drop_column("users", "container_uid")
    op.drop_column("kernels", "gids")
    op.drop_column("kernels", "main_gid")
    op.drop_column("kernels", "uid")
