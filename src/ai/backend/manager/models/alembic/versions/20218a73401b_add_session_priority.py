"""add-session-priority

Revision ID: 20218a73401b
Revises: c4b7ec740b36
Create Date: 2024-09-18 12:22:20.397024

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20218a73401b"
down_revision = "c4b7ec740b36"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("priority", sa.Integer(), server_default=sa.text("10"), nullable=False),
    )
    op.create_index(
        "ix_session_status_with_priority", "sessions", ["status", "priority"], unique=False
    )
    op.create_index(op.f("ix_sessions_priority"), "sessions", ["priority"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sessions_priority"), table_name="sessions")
    op.drop_index("ix_session_status_with_priority", table_name="sessions")
    op.drop_column("sessions", "priority")
