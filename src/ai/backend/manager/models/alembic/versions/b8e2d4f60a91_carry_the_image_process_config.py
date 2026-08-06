"""carry the image process config

Revision ID: b8e2d4f60a91
Revises: f31c6a8e04b7
Create Date: 2026-08-06

"""

import sqlalchemy as sa
from alembic import op

revision = "b8e2d4f60a91"
down_revision = "f31c6a8e04b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "images",
        sa.Column("process_config", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("images", "process_config")
