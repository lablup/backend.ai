"""drop the session, kernel, and agent resource slot columns

The JSONB slot columns on ``sessions``, ``kernels``, and ``agents`` are no longer
read: ``resource_allocations`` serves session and kernel occupancy, and
``agent_resources`` serves agent capacity and occupancy.

Revision ID: a3d17c9b45e2
Revises: c5a91e37d40b
Create Date: 2026-08-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import ResourceSlotColumn

# revision identifiers, used by Alembic.
revision = "a3d17c9b45e2"
down_revision = "c5a91e37d40b"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_USED = "COALESCE(used, requested)"

_DROPPED_COLUMNS = [
    ("sessions", "occupying_slots"),
    ("sessions", "requested_slots"),
    ("kernels", "occupied_slots"),
    ("kernels", "requested_slots"),
    ("agents", "available_slots"),
    ("agents", "occupied_slots"),
]

_KERNEL_BACKFILL = """
    UPDATE kernels SET {column} = COALESCE(agg.slots, '{{}}'::jsonb)
    FROM (
        SELECT kernel_id, jsonb_object_agg(slot_name, trim_scale({source})::text) AS slots
        FROM resource_allocations
        WHERE {source} IS NOT NULL
        GROUP BY kernel_id
    ) AS agg
    WHERE kernels.id = agg.kernel_id
"""

_SESSION_BACKFILL = """
    UPDATE sessions SET {column} = COALESCE(agg.slots, '{{}}'::jsonb)
    FROM (
        SELECT k.session_id, jsonb_object_agg(k.slot_name, trim_scale(k.total)::text) AS slots
        FROM (
            SELECT k2.session_id, ra.slot_name, SUM({source}) AS total
            FROM resource_allocations ra
            JOIN kernels k2 ON k2.id = ra.kernel_id
            WHERE {source} IS NOT NULL
            GROUP BY k2.session_id, ra.slot_name
        ) AS k
        GROUP BY k.session_id
    ) AS agg
    WHERE sessions.id = agg.session_id
"""

_AGENT_BACKFILL = """
    UPDATE agents SET {column} = COALESCE(agg.slots, '{{}}'::jsonb)
    FROM (
        SELECT agent_id, jsonb_object_agg(slot_name, trim_scale({source})::text) AS slots
        FROM agent_resources
        WHERE {source} IS NOT NULL
        GROUP BY agent_id
    ) AS agg
    WHERE agents.id = agg.agent_id
"""


def upgrade() -> None:
    for table, column in _DROPPED_COLUMNS:
        op.drop_column(table, column)


def downgrade() -> None:
    for table, column in _DROPPED_COLUMNS:
        op.add_column(
            table,
            sa.Column(column, ResourceSlotColumn(), nullable=False, server_default="{}"),
        )
    op.execute(_SESSION_BACKFILL.format(column="occupying_slots", source=_USED))
    op.execute(_SESSION_BACKFILL.format(column="requested_slots", source="requested"))
    op.execute(_KERNEL_BACKFILL.format(column="occupied_slots", source=_USED))
    op.execute(_KERNEL_BACKFILL.format(column="requested_slots", source="requested"))
    op.execute(_AGENT_BACKFILL.format(column="available_slots", source="capacity"))
    op.execute(_AGENT_BACKFILL.format(column="occupied_slots", source="COALESCE(used, 0)"))
    for table, column in _DROPPED_COLUMNS:
        op.alter_column(table, column, server_default=None)
