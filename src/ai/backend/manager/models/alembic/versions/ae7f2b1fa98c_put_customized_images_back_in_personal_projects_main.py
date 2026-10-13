"""Put customized images back in personal projects

A customized image is owned by its creator's personal project: the own membership and
the uncapped binding are what let the creator delete it. `d17b4e9c25a8` removed them;
this writes them back for every customized image whose creator still has a personal
project. Re-running it writes nothing new.

The same statements as `d1117da8d8bd`, which sits right after `d17b4e9c25a8` so the 26.9
branch carries it too. A database upgraded past `c7d2fb1e5a90` before it was placed there
never ran it; this runs them again on top of main.

Revision ID: ae7f2b1fa98c
Revises: c568d88b65b5
Create Date: 2026-10-12

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae7f2b1fa98c"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c568d88b65b5"
branch_labels = None
depends_on = None

_OWNED_PAIRS: Final[str] = """
    SELECT member.id AS member_id, scope.id AS scope_id
    FROM images i
    JOIN groups g ON g.type = 'personal' AND g.creator_id = i.creator_id
    JOIN virtual_entities member ON member.entity_type = 'image' AND member.entity_id = i.id
    JOIN virtual_entities scope ON scope.entity_type = 'project' AND scope.entity_id = g.id
    WHERE i.customized
"""

_ADD_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT pair.scope_id, pair.member_id, FALSE FROM ({_OWNED_PAIRS}) pair
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT pair.member_id, pair.scope_id, NULL FROM ({_OWNED_PAIRS}) pair
    ON CONFLICT DO NOTHING
""")

_REMOVE_MEMBERSHIPS: Final = sa.text(f"""
    DELETE FROM entity_memberships em
    USING ({_OWNED_PAIRS}) pair
    WHERE em.virtual_entity_id = pair.scope_id AND em.member_entity_id = pair.member_id
      AND em.capped IS FALSE
""")

_REMOVE_BINDINGS: Final = sa.text(f"""
    DELETE FROM scope_bindings sb
    USING ({_OWNED_PAIRS}) pair
    WHERE sb.virtual_entity_id = pair.member_id AND sb.scope_entity_id = pair.scope_id
      AND sb.permission_cap IS NULL
""")


def add_personal_project_edges(conn: sa.Connection) -> None:
    """Takes its connection so a test can run it against a real database."""
    conn.execute(_ADD_MEMBERSHIPS)
    conn.execute(_ADD_BINDINGS)


def remove_personal_project_edges(conn: sa.Connection) -> None:
    conn.execute(_REMOVE_MEMBERSHIPS)
    conn.execute(_REMOVE_BINDINGS)


def upgrade() -> None:
    add_personal_project_edges(op.get_bind())


def downgrade() -> None:
    remove_personal_project_edges(op.get_bind())
