"""Add local_rank column in Kernels table

Revision ID: 6129745f49b6
Revises: 360af8f33d4e
Create Date: 2022-10-22 15:58:01.518770

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6129745f49b6"
down_revision = "360af8f33d4e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "kernels",
        sa.Column("local_rank", sa.Integer, nullable=False, server_default=sa.text("0")),
    )


def downgrade():
    op.drop_column("kernels", "local_rank")
