"""Put agents in the graph

A heartbeat registered an agent with a plain insert, so no agent has a virtual entity
node. Give each agent one, owned and governed by its resource group, and give a
resource group without a node one.

Revision ID: e8b1d4a7c2f9
Revises: b3e7a1f09c42
Create Date: 2026-09-15

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e8b1d4a7c2f9"  # Part of: NEXT_RELEASE_VERSION
down_revision = "b3e7a1f09c42"
branch_labels = None
depends_on = None

_ADD_NODES: Final = sa.text("""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'resource_group', id FROM scaling_groups
    UNION ALL
    SELECT 'agent', uuid FROM agents
    ON CONFLICT (entity_type, entity_id) DO NOTHING
""")

_ADD_SELF_MEMBERSHIPS: Final = sa.text("""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT id, id, FALSE FROM virtual_entities
    WHERE entity_type IN ('resource_group', 'agent')
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
""")

_ADD_SELF_BINDINGS: Final = sa.text("""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT id, id, NULL FROM virtual_entities
    WHERE entity_type IN ('resource_group', 'agent')
    ON CONFLICT DO NOTHING
""")

_AGENT_AND_GROUP_NODES: Final = """
    SELECT agent_node.id AS agent_node, group_node.id AS group_node
    FROM agents a
    JOIN virtual_entities agent_node
      ON agent_node.entity_type = 'agent' AND agent_node.entity_id = a.uuid
    JOIN virtual_entities group_node
      ON group_node.entity_type = 'resource_group' AND group_node.entity_id = a.resource_group_id
"""

_ADD_GROUP_OWN_EDGES: Final = sa.text(f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT n.group_node, n.agent_node, FALSE FROM ({_AGENT_AND_GROUP_NODES}) n
    ON CONFLICT (virtual_entity_id, member_entity_id) DO UPDATE SET capped = FALSE
""")

_ADD_GROUP_GOVERN_EDGES: Final = sa.text(f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT n.agent_node, n.group_node, NULL FROM ({_AGENT_AND_GROUP_NODES}) n
    ON CONFLICT DO NOTHING
""")


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(_ADD_NODES)
    conn.execute(_ADD_SELF_MEMBERSHIPS)
    conn.execute(_ADD_SELF_BINDINGS)
    conn.execute(_ADD_GROUP_OWN_EDGES)
    conn.execute(_ADD_GROUP_GOVERN_EDGES)


def downgrade() -> None:
    # The edges go with the agent nodes by FK. A resource group node stays: one made
    # before this revision cannot be told apart.
    op.execute("DELETE FROM virtual_entities WHERE entity_type = 'agent'")
