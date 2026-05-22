"""add client_ip to login_history

Revision ID: a1b3e7c2d4f5
Revises: b8a85c96607c
Create Date: 2026-05-20

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

revision = "a1b3e7c2d4f5"
down_revision = "b8a85c96607c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "login_history",
        sa.Column("client_ip", sa.String(length=45), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("login_history", "client_ip")
