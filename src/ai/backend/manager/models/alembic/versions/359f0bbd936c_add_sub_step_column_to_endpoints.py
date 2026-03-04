"""add sub_step column to endpoints

Revision ID: 359f0bbd936c
Revises: 0b1efbb2db84
Create Date: 2026-03-09 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "359f0bbd936c"
down_revision = "0b1efbb2db84"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoints",
        sa.Column("sub_step", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("endpoints", "sub_step")
