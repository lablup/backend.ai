"""add endpoints.retries

Revision ID: ae7d4cd92aa7
Revises: eb9441fcf90a
Create Date: 2023-08-08 07:30:27.881248

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae7d4cd92aa7"
down_revision = "eb9441fcf90a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "endpoints", sa.Column("retries", sa.Integer, nullable=False, default=0, server_default="0")
    )


def downgrade():
    op.drop_column("endpoint", "retries")
