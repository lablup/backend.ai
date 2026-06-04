"""add replica_id to sessions

Revision ID: 169cb5f48658
Revises: eb9d9c018e85
Create Date: 2026-06-04 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "169cb5f48658"
down_revision = "eb9d9c018e85"
# Part of: 26.6.0
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("replica_id", GUID(), nullable=True),
    )
    # Backfill from the inverse link (routings.session -> sessions.id). A session
    # serves at most one replica; pick the earliest route deterministically.
    # Idempotent: only fills rows still NULL.
    op.execute(
        sa.text(
            """
            UPDATE sessions
            SET replica_id = (
                SELECT routings.id
                FROM routings
                WHERE routings.session = sessions.id
                ORDER BY routings.created_at ASC, routings.id ASC
                LIMIT 1
            )
            WHERE sessions.replica_id IS NULL
              AND EXISTS (
                SELECT 1 FROM routings WHERE routings.session = sessions.id
              )
            """
        )
    )


def downgrade() -> None:
    op.drop_column("sessions", "replica_id")
