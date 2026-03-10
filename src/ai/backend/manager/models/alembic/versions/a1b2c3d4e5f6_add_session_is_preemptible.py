"""add-session-is-preemptible

Revision ID: a1b2c3d4e5f6
Revises: b1009fe7f865
Create Date: 2026-03-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.common.defs.session import SESSION_IS_PREEMPTIBLE_DEFAULT

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "b1009fe7f865"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("is_preemptible", sa.Boolean(), nullable=True),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE sessions SET is_preemptible = :val WHERE is_preemptible IS NULL"),
        {"val": SESSION_IS_PREEMPTIBLE_DEFAULT},
    )
    op.alter_column("sessions", "is_preemptible", nullable=False)


def downgrade() -> None:
    op.drop_column("sessions", "is_preemptible")
