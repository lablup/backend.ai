"""Put vfolders in the graph

A folder made before virtual entities existed has no node, and the earlier revisions
gave one only to a folder with a pending invitation or a legacy permission row. Give
every folder a node owned and governed by the project its ``group`` column names: the
personal project for a user-owned folder, its project for a group-owned one.

Revision ID: dafe06a6c763
Revises: a7d0f5b3c841
Create Date: 2026-09-16

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dafe06a6c763"  # Part of: NEXT_RELEASE_VERSION
down_revision = "a7d0f5b3c841"
branch_labels = None
depends_on = None

_ADD_FOLDER_NODES: Final = sa.text("""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'vfolder', id FROM vfolders
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

# A node owns and governs itself, the way a created entity's does.
_ADD_SELF_MEMBERSHIPS: Final = sa.text("""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT id, id, FALSE FROM virtual_entities
    WHERE entity_type = 'vfolder'
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SELF_BINDINGS: Final = sa.text("""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT id, id, NULL FROM virtual_entities
    WHERE entity_type = 'vfolder'
    ON CONFLICT DO NOTHING
""")

_FOLDER_AND_PROJECT_NODES: Final = """
    SELECT folder_node.id AS folder_node, project_node.id AS project_node
    FROM vfolders v
    JOIN virtual_entities folder_node
      ON folder_node.entity_type = 'vfolder' AND folder_node.entity_id = v.id
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = v."group"
"""

_ADD_PROJECT_OWN_EDGES: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.project_node, n.folder_node, FALSE FROM ({_FOLDER_AND_PROJECT_NODES}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_PROJECT_GOVERN_EDGES: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.folder_node, n.project_node, NULL FROM ({_FOLDER_AND_PROJECT_NODES}) n
    ON CONFLICT DO NOTHING
""")


def put_vfolders_in_the_graph(conn: sa.Connection) -> None:
    conn.execute(_ADD_FOLDER_NODES)
    conn.execute(_ADD_SELF_MEMBERSHIPS)
    conn.execute(_ADD_SELF_BINDINGS)
    conn.execute(_ADD_PROJECT_OWN_EDGES)
    conn.execute(_ADD_PROJECT_GOVERN_EDGES)


def upgrade() -> None:
    put_vfolders_in_the_graph(op.get_bind())


def downgrade() -> None:
    # Nothing is removed: a node or edge this revision added cannot be told apart from
    # one a folder creation made.
    pass
