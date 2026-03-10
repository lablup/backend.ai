"""add-session-is-preemptible

Revision ID: 6f2f5d828a52
Revises: b1009fe7f865
Create Date: 2026-03-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6f2f5d828a52"
down_revision = "b1009fe7f865"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("is_preemptible", sa.Boolean(), nullable=True, server_default=sa.text("true")),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE sessions SET is_preemptible = true WHERE is_preemptible IS NULL"),
    )
    op.alter_column("sessions", "is_preemptible", nullable=False)


def downgrade() -> None:
    op.drop_column("sessions", "is_preemptible")
