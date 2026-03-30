"""drop expires_at from login_sessions

Revision ID: 17b679c98b50
Revises: 21ce28a1c771
Create Date: 2026-03-26 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "17b679c98b50"
down_revision = "21ce28a1c771"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(op.f("ix_login_sessions_expires_at"), table_name="login_sessions")
    op.drop_column("login_sessions", "expires_at")


def downgrade() -> None:
    op.add_column(
        "login_sessions",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Backfill expires_at for existing rows using created_at + 7 days
    op.execute(
        "UPDATE login_sessions SET expires_at = created_at + INTERVAL '7 days' WHERE expires_at IS NULL"
    )
    op.alter_column("login_sessions", "expires_at", nullable=False)
    op.create_index(op.f("ix_login_sessions_expires_at"), "login_sessions", ["expires_at"])
