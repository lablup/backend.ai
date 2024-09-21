"""add-session-priority

Revision ID: 20218a73401b
Revises: 3596bc12ec09
Create Date: 2024-09-18 12:22:20.397024

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.session import SESSION_PRIORITY_DEFUALT

# revision identifiers, used by Alembic.
revision = "20218a73401b"
down_revision = "3596bc12ec09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # To allow changing SESSION_PRIORITY_DEFUALT in the future, add the new column with the
    # python-side default only without fixing the database-side default.
    op.add_column(
        "sessions",
        sa.Column("priority", sa.Integer(), nullable=True),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE sessions SET priority = :priority WHERE priority IS NULL"),
        {"priority": SESSION_PRIORITY_DEFUALT},
    )
    op.alter_column("sessions", "priority", nullable=False)
    op.create_index(
        "ix_session_status_with_priority", "sessions", ["status", "priority"], unique=False
    )
    op.create_index(op.f("ix_sessions_priority"), "sessions", ["priority"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sessions_priority"), table_name="sessions")
    op.drop_index("ix_session_status_with_priority", table_name="sessions")
    op.drop_column("sessions", "priority")
