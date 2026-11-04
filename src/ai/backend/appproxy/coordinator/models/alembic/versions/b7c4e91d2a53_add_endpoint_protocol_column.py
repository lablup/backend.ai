"""add endpoint protocol column

Revision ID: b7c4e91d2a53
Revises: a1b2c3d4e5f6
Create Date: 2026-10-14 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c4e91d2a53"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoints",
        sa.Column(
            "protocol",
            sa.String(length=64),
            nullable=False,
            server_default="http",
        ),
    )


def downgrade() -> None:
    op.drop_column("endpoints", "protocol")
