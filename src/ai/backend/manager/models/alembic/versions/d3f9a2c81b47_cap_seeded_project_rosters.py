"""Cap the project roster edges a seed wrote

A roster edge the runtime writes is a share capped to read; one written by the account
seed was an owning edge, which lends every bit a project-scoped role holds. Turn the
uncapped edges into the shape the runtime writes.

Revision ID: d3f9a2c81b47
Revises: c4b1f7e9a2d3
Create Date: 2026-09-22

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d3f9a2c81b47"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c4b1f7e9a2d3"
branch_labels = None
depends_on = None

_READ: Final[int] = 1

_ROSTER_EDGES: Final[str] = """
    SELECT m.id, m.capped
    FROM entity_memberships m
    JOIN virtual_entities p ON p.id = m.virtual_entity_id AND p.entity_type = 'project'
    JOIN virtual_entities u ON u.id = m.member_entity_id AND u.entity_type = 'user'
"""

_CAP_EDGES: Final = sa.text(f"""
    UPDATE entity_memberships SET capped = TRUE
    WHERE id IN (SELECT id FROM ({_ROSTER_EDGES}) e WHERE NOT e.capped)
""")

_ADD_READ_CAPS: Final = sa.text(f"""
    INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
    SELECT e.id, {_READ}, TRUE FROM ({_ROSTER_EDGES}) e WHERE e.capped
    ON CONFLICT (membership_id, permission) DO NOTHING
""")


def cap_project_rosters(conn: sa.Connection) -> None:
    """Every project roster edge is capped and lends read. Idempotent: an edge the
    runtime wrote already holds that cap and keeps it."""
    conn.execute(_CAP_EDGES)
    conn.execute(_ADD_READ_CAPS)


def upgrade() -> None:
    cap_project_rosters(op.get_bind())


def downgrade() -> None:
    # Nothing is put back: an uncapped roster edge cannot be told apart from one this
    # revision capped.
    pass
