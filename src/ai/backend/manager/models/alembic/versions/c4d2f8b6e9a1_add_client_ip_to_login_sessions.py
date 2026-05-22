"""add client_ip to login_sessions

Revision ID: c4d2f8b6e9a1
Revises: a1b3e7c2d4f5
Create Date: 2026-05-22

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

revision = "c4d2f8b6e9a1"
down_revision = "a1b3e7c2d4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "login_sessions",
        sa.Column("client_ip", sa.String(length=45), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("login_sessions", "client_ip")
