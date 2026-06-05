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
    # Backfill: set replica_id to each session's earliest live route (DISTINCT ON
    # picks one per session). Only active routes count (RouteStatus provisioning/
    # running); sessions with no live route stay NULL. Status is stored as the enum
    # value (StrEnumType, use_name=False), hence the lowercase literals.
    op.execute(
        sa.text(
            """
            UPDATE sessions
            SET replica_id = r.id
            FROM (
                SELECT DISTINCT ON (routings.session)
                    routings.session AS session_id,
                    routings.id
                FROM routings
                WHERE routings.status IN ('provisioning', 'running')
                ORDER BY routings.session, routings.created_at ASC, routings.id ASC
            ) AS r
            WHERE sessions.id = r.session_id
            """
        )
    )
    # FK to routings.id with ON DELETE SET NULL so a deleted replica route clears
    # the pointer instead of leaving a dangling id. Created after the backfill,
    # which only writes existing (live) route ids, so the constraint validates.
    op.create_foreign_key(
        "fk_sessions_replica_id_routings",
        "sessions",
        "routings",
        ["replica_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_sessions_replica_id_routings", "sessions", type_="foreignkey")
    op.drop_column("sessions", "replica_id")
