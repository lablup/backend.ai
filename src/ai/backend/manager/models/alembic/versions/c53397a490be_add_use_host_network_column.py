"""add use_host_network column

Revision ID: c53397a490be
Revises: 360af8f33d4e
Create Date: 2022-10-25 17:02:31.709513

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c53397a490be"
down_revision = "360af8f33d4e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "kernels", sa.Column("use_host_network", sa.BOOLEAN(), nullable=False, default=False)
    )


def downgrade():
    op.drop_column("kernels", "use_host_network")
