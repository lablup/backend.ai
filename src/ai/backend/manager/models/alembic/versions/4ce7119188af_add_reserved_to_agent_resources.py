"""add reserved column to agent_resources

Adds a ``reserved`` column to ``agent_resources`` so resource allocation can be
gated at the table level: scheduling increments ``reserved`` (scheduled but not
yet running), the RUNNING transition moves it into ``used``, and the invariant
``reserved + used <= capacity`` is enforced atomically.

Backfills ``reserved`` from the sum of active, not-yet-running allocation
requests (``resource_allocations.requested`` where ``free_at IS NULL`` and
``used_at IS NULL``) grouped per agent and slot.

Create Date: 2026-05-26

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4ce7119188af"
down_revision = "b8a85c96607c"
# Part of: 26.5.1
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_resources",
        sa.Column(
            "reserved",
            sa.Numeric(precision=24, scale=6),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    # Backfill reserved from scheduled-but-not-running allocations.
    op.execute("""
        UPDATE agent_resources ar
        SET reserved = sub.total
        FROM (
            SELECT k.agent AS agent_id, ra.slot_name AS slot_name, SUM(ra.requested) AS total
            FROM resource_allocations ra
            JOIN kernels k ON k.id = ra.kernel_id
            WHERE ra.free_at IS NULL
              AND ra.used_at IS NULL
              AND k.agent IS NOT NULL
            GROUP BY k.agent, ra.slot_name
        ) AS sub
        WHERE ar.agent_id = sub.agent_id
          AND ar.slot_name = sub.slot_name
    """)

    # Recreate the availability covering index to include reserved.
    op.drop_index("ix_agent_resources_agent_avail", table_name="agent_resources")
    op.create_index(
        "ix_agent_resources_agent_avail",
        "agent_resources",
        ["agent_id", "slot_name", "capacity", "reserved", "used"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_agent_resources_agent_avail", table_name="agent_resources")
    op.create_index(
        "ix_agent_resources_agent_avail",
        "agent_resources",
        ["agent_id", "slot_name", "capacity", "used"],
        unique=False,
    )
    op.drop_column("agent_resources", "reserved")
