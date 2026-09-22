"""Backfill model card creator edges

A model card is created in its project and in the user who created it. Cards on file
have the project edge alone; write the creator edge the runtime writes now.

Revision ID: e7a3c1d95f42
Revises: d6e2b7a4c913
Create Date: 2026-09-21

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7a3c1d95f42"  # Part of: NEXT_RELEASE_VERSION
down_revision = "d6e2b7a4c913"
branch_labels = None
depends_on = None

CHUNK_SIZE: Final[int] = 1000

# (card node, creator node) of one page of cards. A card whose creator or
# whose own node is missing names no pair.
_PAIRS: Final[str] = """
    SELECT node.id AS node, scope.id AS scope
    FROM model_cards mc
    JOIN virtual_entities node
      ON node.entity_type = 'model_card' AND node.entity_id = mc.id
    JOIN virtual_entities scope
      ON scope.entity_type = 'user' AND scope.entity_id = mc.creator
    WHERE mc.id = ANY(CAST(:card_ids AS uuid[]))
"""

_NEXT_CARD_IDS: Final = sa.text("""
    SELECT id FROM model_cards
    WHERE CAST(:after AS uuid) IS NULL OR id > CAST(:after AS uuid)
    ORDER BY id
    LIMIT :limit
""")

_ADD_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.scope, n.node, FALSE FROM ({_PAIRS}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.node, n.scope, NULL FROM ({_PAIRS}) n
    ON CONFLICT DO NOTHING
""")

_REMOVE_MEMBERSHIPS: Final = sa.text(f"""
    DELETE FROM entity_memberships em
    USING ({_PAIRS}) n
    WHERE em.virtual_entity_id = n.scope
      AND em.member_entity_id = n.node
      AND em.capped IS FALSE
""")

_REMOVE_BINDINGS: Final = sa.text(f"""
    DELETE FROM scope_bindings sb
    USING ({_PAIRS}) n
    WHERE sb.virtual_entity_id = n.node
      AND sb.scope_entity_id = n.scope
      AND sb.permission_cap IS NULL
""")


def _for_each_chunk(conn: sa.Connection, statements: tuple[sa.TextClause, ...]) -> None:
    after = None
    while True:
        card_ids = (
            conn.execute(_NEXT_CARD_IDS, {"after": after, "limit": CHUNK_SIZE}).scalars().all()
        )
        if not card_ids:
            return
        for statement in statements:
            conn.execute(statement, {"card_ids": card_ids})
        after = card_ids[-1]


def add_creator_edges(conn: sa.Connection) -> None:
    _for_each_chunk(conn, (_ADD_MEMBERSHIPS, _ADD_BINDINGS))


def remove_creator_edges(conn: sa.Connection) -> None:
    _for_each_chunk(conn, (_REMOVE_MEMBERSHIPS, _REMOVE_BINDINGS))


def upgrade() -> None:
    add_creator_edges(op.get_bind())


def downgrade() -> None:
    remove_creator_edges(op.get_bind())
