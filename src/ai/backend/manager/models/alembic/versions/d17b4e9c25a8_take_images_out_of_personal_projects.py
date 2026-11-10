"""Take images out of personal projects

An image belongs to the registry it was scanned from, and to `public` as well where that
registry is global. A customized one is no exception: it is the same kind of row in the
same registry, and who may see it is a read's question rather than a membership. The
graph backfill placed every customized image in its creator's personal project as well,
so those edges go.

The set is bounded by the number of session commits on file, so the statements are not
paged. Shares are untouched: only an own membership (`capped IS FALSE`) and an uncapped
binding are taken back, and no scope other than a personal project ever owned an image.

Revision ID: d17b4e9c25a8
Revises: a91c4e7d0b35
Create Date: 2026-09-28

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

revision = "d17b4e9c25a8"  # Part of: 26.9.0
down_revision = "a91c4e7d0b35"
branch_labels = None
depends_on = None

# Whatever project owns an image, the edge goes: the backfill wrote the creator's
# personal project, and a creator since purged leaves the edge naming a project no column
# derives any more. Each statement reads its own table alone, so neither depends on the
# other having run.

# The pairs the backfill wrote, derived the way it derived them.
_BACKFILLED_PAIRS: Final[str] = """
    SELECT member.id AS member_id, scope.id AS scope_id
    FROM images i
    JOIN groups g ON g.type = 'personal' AND g.creator_id = i.creator_id
    JOIN virtual_entities member ON member.entity_type = 'image' AND member.entity_id = i.id
    JOIN virtual_entities scope ON scope.entity_type = 'project' AND scope.entity_id = g.id
    WHERE i.customized
"""

_REMOVE_MEMBERSHIPS: Final = sa.text("""
    DELETE FROM entity_memberships em
    USING virtual_entities scope, virtual_entities member
    WHERE em.virtual_entity_id = scope.id AND scope.entity_type = 'project'
      AND em.member_entity_id = member.id AND member.entity_type = 'image'
      AND em.capped IS FALSE
""")

_REMOVE_BINDINGS: Final = sa.text("""
    DELETE FROM scope_bindings sb
    USING virtual_entities scope, virtual_entities member
    WHERE sb.scope_entity_id = scope.id AND scope.entity_type = 'project'
      AND sb.virtual_entity_id = member.id AND member.entity_type = 'image'
      AND sb.permission_cap IS NULL
""")

_ADD_MEMBERSHIPS: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT pair.scope_id, pair.member_id, FALSE FROM ({_BACKFILLED_PAIRS}) pair
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_BINDINGS: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT pair.member_id, pair.scope_id, NULL FROM ({_BACKFILLED_PAIRS}) pair
    ON CONFLICT DO NOTHING
""")


def remove_project_edges(conn: sa.Connection) -> None:
    """Every image leaves the project that owned it. Takes its connection so a test can
    run it against a real database — static analysis does not reach SQL."""
    conn.execute(_REMOVE_MEMBERSHIPS)
    conn.execute(_REMOVE_BINDINGS)


def add_project_edges(conn: sa.Connection) -> None:
    """The reverse: every customized image rejoins the personal project of the user it
    was committed for, where that user still has one."""
    conn.execute(_ADD_MEMBERSHIPS)
    conn.execute(_ADD_BINDINGS)


def upgrade() -> None:
    remove_project_edges(op.get_bind())


def downgrade() -> None:
    add_project_edges(op.get_bind())
