"""Move session designated agents to a table

`sessions.designated_agent_ids` held `agents.id` strings with no foreign key. Each one
becomes a `session_designated_agents` row naming `agents.uuid`, and the column goes.

An id missing from `agents` designates nothing and is dropped. A pending STRICT session
holding one could never be placed, so it is cancelled the way the scheduler cancels a
pending session: the session and its kernels, and the kernels' allocations freed.

Revision ID: c5ea6e2fa389
Revises: 111e2255487b
Create Date: 2026-10-19 21:00:00.000000

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c5ea6e2fa389"
down_revision = "111e2255487b"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

CANCEL_REASON: Final[str] = "designated-agent-missing"

_CANCEL_SESSIONS: Final = sa.text("""
    UPDATE sessions
    SET status = 'CANCELLED',
        status_info = :reason,
        terminated_at = now(),
        status_history = COALESCE(status_history, '{}'::jsonb)
            || jsonb_build_object('CANCELLED', to_jsonb(now()))
    WHERE status = 'PENDING'
      AND options->>'agent_selection_policy' = 'strict'
      AND EXISTS (
        SELECT 1 FROM unnest(designated_agent_ids) AS designated(agent_id)
        WHERE NOT EXISTS (SELECT 1 FROM agents WHERE agents.id = designated.agent_id)
      )
    RETURNING id
""")

_CANCEL_KERNELS: Final = sa.text("""
    UPDATE kernels
    SET status = 'CANCELLED',
        status_info = :reason,
        status_changed = now(),
        terminated_at = now(),
        status_history = COALESCE(status_history, '{}'::jsonb)
            || jsonb_build_object('CANCELLED', to_jsonb(now()))
    WHERE session_id = ANY(CAST(:session_ids AS uuid[]))
    RETURNING id
""")

_FREE_ALLOCATIONS: Final = sa.text("""
    UPDATE resource_allocations
    SET free_at = now()
    WHERE kernel_id = ANY(CAST(:kernel_ids AS uuid[])) AND free_at IS NULL
""")

_BACKFILL: Final = sa.text("""
    INSERT INTO session_designated_agents (session_id, agent_uuid)
    SELECT sessions.id, agents.uuid
    FROM sessions
    CROSS JOIN LATERAL unnest(sessions.designated_agent_ids) AS designated(agent_id)
    JOIN agents ON agents.id = designated.agent_id
    ON CONFLICT DO NOTHING
""")

_RESTORE_ARRAYS: Final = sa.text("""
    UPDATE sessions
    SET designated_agent_ids = designated.agent_ids
    FROM (
        SELECT session_designated_agents.session_id, array_agg(agents.id) AS agent_ids
        FROM session_designated_agents
        JOIN agents ON agents.uuid = session_designated_agents.agent_uuid
        GROUP BY session_designated_agents.session_id
    ) AS designated
    WHERE sessions.id = designated.session_id
""")


def cancel_unplaceable_sessions(conn: sa.Connection) -> None:
    """Cancel the pending STRICT sessions designating an agent missing from `agents`."""
    session_ids = [str(row.id) for row in conn.execute(_CANCEL_SESSIONS, {"reason": CANCEL_REASON})]
    if not session_ids:
        return
    kernel_ids = [
        str(row.id)
        for row in conn.execute(
            _CANCEL_KERNELS, {"reason": CANCEL_REASON, "session_ids": session_ids}
        )
    ]
    if kernel_ids:
        conn.execute(_FREE_ALLOCATIONS, {"kernel_ids": kernel_ids})


def backfill_designations(conn: sa.Connection) -> None:
    """Write a row per designated agent still in `agents`."""
    conn.execute(_BACKFILL)


def restore_designations(conn: sa.Connection) -> None:
    """Write the rows back into the array column."""
    conn.execute(_RESTORE_ARRAYS)


def upgrade() -> None:
    op.create_table(
        "session_designated_agents",
        sa.Column(
            "id",
            GUID(),
            server_default=sa.text("uuid_generate_v7()"),
            nullable=False,
        ),
        sa.Column("session_id", GUID(), nullable=False),
        sa.Column("agent_uuid", GUID(), nullable=False),
        sa.PrimaryKeyConstraint(
            "session_id", "agent_uuid", name=op.f("pk_session_designated_agents")
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_session_designated_agents_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_uuid"],
            ["agents.uuid"],
            name=op.f("fk_session_designated_agents_agent_uuid_agents"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("id", name=op.f("uq_session_designated_agents_id")),
    )
    op.create_index(
        op.f("ix_session_designated_agents_agent_uuid"),
        "session_designated_agents",
        ["agent_uuid"],
        unique=False,
    )
    conn = op.get_bind()
    cancel_unplaceable_sessions(conn)
    backfill_designations(conn)
    op.drop_column("sessions", "designated_agent_ids")


def downgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("designated_agent_ids", sa.ARRAY(sa.String()), nullable=True),
    )
    restore_designations(op.get_bind())
    op.drop_index(
        op.f("ix_session_designated_agents_agent_uuid"),
        table_name="session_designated_agents",
    )
    op.drop_table("session_designated_agents")
