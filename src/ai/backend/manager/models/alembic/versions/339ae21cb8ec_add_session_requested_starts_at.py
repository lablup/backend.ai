"""add sessions.requested_starts_at

``sessions.starts_at`` carried two meanings: the reserved start time written
at enqueue for batch sessions, and the actual execution start time written at
the RUNNING transition (overwriting the former). Split the reserved meaning
into a new ``requested_starts_at`` column; ``starts_at`` keeps the execution
meaning.

Backfill: batch sessions that have not reached RUNNING yet still hold the
reserved time in ``starts_at``, so copy it over. For sessions that already
ran (or terminated), the reserved time was overwritten and is lost — leave
``requested_starts_at`` NULL.

Revision ID: 339ae21cb8ec
Revises: b3e8f1a24c76
Create Date: 2026-07-23

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "339ae21cb8ec"
down_revision = "b3e8f1a24c76"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

PRE_RUNNING_STATUSES = (
    "PENDING",
    "DEPRIORITIZING",
    "SCHEDULED",
    "PREPARING",
    "PULLING",
    "PREPARED",
    "CREATING",
)


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("requested_starts_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE sessions
            SET requested_starts_at = starts_at
            WHERE session_type = 'BATCH'
              AND starts_at IS NOT NULL
              AND status IN :statuses
            """
        ).bindparams(sa.bindparam("statuses", PRE_RUNNING_STATUSES, expanding=True))
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE sessions
            SET starts_at = requested_starts_at
            WHERE requested_starts_at IS NOT NULL
              AND status IN :statuses
            """
        ).bindparams(sa.bindparam("statuses", PRE_RUNNING_STATUSES, expanding=True))
    )
    op.drop_column("sessions", "requested_starts_at")
