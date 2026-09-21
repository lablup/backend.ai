"""Backfill the resource group membership of bound resource presets

A preset bound to a resource group is read at that group's scope, so it has to belong
to the group for an id read to pass. The rows on file belong to `global` alone.

Revision ID: b8d14e6a0f52
Revises: a3f60d2b7c19
Create Date: 2026-09-21

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b8d14e6a0f52"  # Part of: NEXT_RELEASE_VERSION
down_revision = "a3f60d2b7c19"
branch_labels = None
depends_on = None

CHUNK_SIZE: Final[int] = 1000

# One page of bound presets, paired with the node of the group each is bound to. A
# preset or a group without a node contributes nothing.
_PAIRS: Final[str] = """
    SELECT preset_node.id AS member_id, group_node.id AS scope_id
    FROM resource_presets p
    JOIN scaling_groups g ON g.name = p.scaling_group_name
    JOIN virtual_entities preset_node
      ON preset_node.entity_type = 'resource_preset' AND preset_node.entity_id = p.id
    JOIN virtual_entities group_node
      ON group_node.entity_type = 'resource_group' AND group_node.entity_id = g.id
    WHERE p.id = ANY(CAST(:preset_ids AS uuid[]))
"""

_ADD_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT pair.scope_id, pair.member_id, FALSE FROM ({_PAIRS}) pair
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT pair.member_id, pair.scope_id, NULL FROM ({_PAIRS}) pair
    ON CONFLICT DO NOTHING
""")

_REMOVE_MEMBERSHIPS: Final = sa.text(f"""
    DELETE FROM entity_memberships em
    USING ({_PAIRS}) pair
    WHERE em.virtual_entity_id = pair.scope_id
      AND em.member_entity_id = pair.member_id
      AND em.capped IS FALSE
""")

_REMOVE_BINDINGS: Final = sa.text(f"""
    DELETE FROM scope_bindings sb
    USING ({_PAIRS}) pair
    WHERE sb.virtual_entity_id = pair.member_id
      AND sb.scope_entity_id = pair.scope_id
      AND sb.permission_cap IS NULL
""")

_PAGE: Final = sa.text("""
    SELECT p.id
    FROM resource_presets p
    WHERE p.scaling_group_name IS NOT NULL
      AND (CAST(:after AS uuid) IS NULL OR p.id > CAST(:after AS uuid))
    ORDER BY p.id
    LIMIT :limit
""")


def _for_each_chunk(conn: sa.Connection, statements: tuple[sa.TextClause, ...]) -> None:
    after = None
    while True:
        preset_ids = conn.execute(_PAGE, {"after": after, "limit": CHUNK_SIZE}).scalars().all()
        if not preset_ids:
            break
        for statement in statements:
            conn.execute(statement, {"preset_ids": list(preset_ids)})
        after = preset_ids[-1]


def add_group_edges(conn: sa.Connection) -> None:
    _for_each_chunk(conn, (_ADD_MEMBERSHIPS, _ADD_BINDINGS))


def remove_group_edges(conn: sa.Connection) -> None:
    _for_each_chunk(conn, (_REMOVE_MEMBERSHIPS, _REMOVE_BINDINGS))


def upgrade() -> None:
    add_group_edges(op.get_bind())


def downgrade() -> None:
    remove_group_edges(op.get_bind())
