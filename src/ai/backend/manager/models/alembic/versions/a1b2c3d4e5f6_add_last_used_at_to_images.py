"""add last_used_at to images

Revision ID: a1b2c3d4e5f6
Revises: ffcf0ed13a26
Create Date: 2026-03-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "ffcf0ed13a26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "images",
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("images", "last_used_at")
