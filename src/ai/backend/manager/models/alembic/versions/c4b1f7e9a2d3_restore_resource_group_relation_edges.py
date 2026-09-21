"""Restore the relation edges of resource groups

An installation that wrote a resource group association without its graph edges reads
nothing at that group's scope. Write the edges every association on file stands for.

Revision ID: c4b1f7e9a2d3
Revises: a1f6b7c4d902
Create Date: 2026-09-21

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4b1f7e9a2d3"  # Part of: NEXT_RELEASE_VERSION
down_revision = "a1f6b7c4d902"
branch_labels = None
depends_on = None

_READ: Final[int] = 1

# The scope each association names, read as (resource group, scope type, scope id).
RELATION_SOURCES: Final[tuple[str, ...]] = (
    "SELECT resource_group_id, 'domain', domain_id FROM sgroups_for_domains",
    """SELECT resource_group_id, 'project', "group" FROM sgroups_for_groups""",
    """SELECT s.resource_group_id, 'user', k."user" FROM sgroups_for_keypairs s"""
    " JOIN keypairs k ON k.access_key = s.access_key",
)


def _node_pairs(source: str) -> str:
    """The distinct (resource group node, scope node) pairs a source names."""
    return f"""
        SELECT DISTINCT node.id AS node, scope.id AS scope
        FROM ({source}) s (entity_id, scope_type, scope_id)
        JOIN virtual_entities node
          ON node.entity_type = 'resource_group' AND node.entity_id = s.entity_id
        JOIN virtual_entities scope
          ON scope.entity_type = s.scope_type AND scope.entity_id = s.scope_id
    """


def add_relation_edges(conn: sa.Connection) -> None:
    """The scope governs the resource group under READ; the group holds READ on the
    scope. Idempotent, so a deployment already holding the edges is unchanged."""
    for source in RELATION_SOURCES:
        pairs = _node_pairs(source)
        conn.execute(
            sa.text(f"""
                INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
                SELECT n.node, n.scope, {_READ} FROM ({pairs}) n
                ON CONFLICT DO NOTHING
            """)
        )
        conn.execute(
            sa.text(f"""
                INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
                SELECT n.node, n.scope, TRUE FROM ({pairs}) n
                ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
            """)
        )
        conn.execute(
            sa.text(f"""
                INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
                SELECT m.id, {_READ}, TRUE
                FROM ({pairs}) n
                JOIN entity_memberships m
                  ON m.virtual_entity_id = n.node AND m.member_entity_id = n.scope
                WHERE m.capped
                ON CONFLICT (membership_id, permission) DO UPDATE SET all_fields = TRUE
            """)
        )


def upgrade() -> None:
    add_relation_edges(op.get_bind())


def downgrade() -> None:
    # Nothing is removed: a row this revision added cannot be told apart from one an
    # association written through the relation ops made.
    pass
