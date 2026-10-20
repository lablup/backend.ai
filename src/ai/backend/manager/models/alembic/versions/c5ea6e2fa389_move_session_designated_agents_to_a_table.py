"""Move session designated agents to a table

`sessions.designated_agent_ids` held `agents.id` strings with no foreign key. Each one
becomes a `session_designated_agents` row naming `agents.uuid`, and the column goes.

An id missing from `agents` designates nothing and is dropped. A pending STRICT session
holding one could never be placed, so it is cancelled the way the scheduler cancels a
pending session: the session and its kernels, and the kernels' allocations freed.

Revision ID: c5ea6e2fa389
Revises: c7e2a91f4d36
Create Date: 2026-10-19 21:00:00.000000

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c5ea6e2fa389"
down_revision = "c7e2a91f4d36"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

CANCEL_REASON: Final[str] = "designated-agent-missing"


def move_designations(conn: sa.Connection) -> None:
    """Cancel the pending STRICT sessions designating a missing agent, then write the rows."""
    conn.execute(
        sa.text("""
            WITH cancelled_sessions AS (
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
            ), cancelled_kernels AS (
                UPDATE kernels
                SET status = 'CANCELLED',
                    status_info = :reason,
                    status_changed = now(),
                    terminated_at = now(),
                    status_history = COALESCE(status_history, '{}'::jsonb)
                        || jsonb_build_object('CANCELLED', to_jsonb(now()))
                WHERE session_id IN (SELECT id FROM cancelled_sessions)
                RETURNING id
            )
            UPDATE resource_allocations
            SET free_at = now()
            WHERE kernel_id IN (SELECT id FROM cancelled_kernels) AND free_at IS NULL
        """),
        {"reason": CANCEL_REASON},
    )
    conn.execute(
        sa.text("""
            INSERT INTO session_designated_agents (session_id, agent_uuid)
            SELECT sessions.id, agents.uuid
            FROM sessions
            CROSS JOIN LATERAL unnest(sessions.designated_agent_ids) AS designated(agent_id)
            JOIN agents ON agents.id = designated.agent_id
            ON CONFLICT DO NOTHING
        """)
    )


def restore_designations(conn: sa.Connection) -> None:
    """Write the rows back into the array column."""
    conn.execute(
        sa.text("""
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
    )


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
    move_designations(op.get_bind())
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
