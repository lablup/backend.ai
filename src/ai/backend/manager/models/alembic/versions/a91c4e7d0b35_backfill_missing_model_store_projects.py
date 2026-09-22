"""Backfill the model-store project a domain is registered with

Creating a domain wrote its model-store project in the REST and GraphQL `createDomain`
handlers, so a domain created through `createDomainNode` has none. Register one for each
domain that is missing it, put it in the graph under its domain, lend it the resource
policy it is subject to, and put the domain's users on its roster.

The roles the project's presets call for are created by `mgr permissions provision`,
the way every other scope gets them.

Revision ID: a91c4e7d0b35
Revises: c7a3f18d6b04
Create Date: 2026-09-22

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a91c4e7d0b35"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c7a3f18d6b04"
branch_labels = None
depends_on = None

_READ: Final[int] = 1
_PROJECT_TYPE: Final[str] = "model-store"
_POLICY_NAME: Final[str] = "default"

# Every statement below keys on the model-store projects themselves rather than on what
# this revision inserted, so a run that stopped part way can be repeated.
_MODEL_STORE_PROJECTS: Final[str] = f"""
    SELECT g.id AS project_id, g.domain_name AS domain_name
    FROM groups g
    WHERE g.type = '{_PROJECT_TYPE}'
"""

_ADD_PROJECTS: Final[str] = f"""
    INSERT INTO groups (
        name, description, is_active, status, domain_name,
        total_resource_slots, allowed_vfolder_hosts, dotfiles, resource_policy, type
    )
    SELECT
        '{_PROJECT_TYPE}', 'Model Store', TRUE, 'active', d.name,
        '{{}}'::jsonb, '{{}}'::jsonb, '\\x90'::bytea, p.name, '{_PROJECT_TYPE}'
    FROM domains d
    JOIN project_resource_policies p ON p.name = :policy_name
    WHERE NOT EXISTS (
        SELECT 1 FROM groups g
        WHERE g.domain_name = d.name AND g.type = '{_PROJECT_TYPE}'
    )
"""

_ADD_NODES: Final[str] = f"""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'project', s.project_id FROM ({_MODEL_STORE_PROJECTS}) s
    ON CONFLICT (entity_type, entity_id) DO NOTHING
"""

_ADD_SELF_EDGES: Final[str] = f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT node.id, node.id, FALSE
    FROM ({_MODEL_STORE_PROJECTS}) s
    JOIN virtual_entities node ON node.entity_type = 'project' AND node.entity_id = s.project_id
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
"""

_ADD_SELF_BINDINGS: Final[str] = f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT node.id, node.id, NULL
    FROM ({_MODEL_STORE_PROJECTS}) s
    JOIN virtual_entities node ON node.entity_type = 'project' AND node.entity_id = s.project_id
    ON CONFLICT DO NOTHING
"""

# The domain the project was created in owns and governs it.
_ADD_DOMAIN_OWNERSHIP: Final[str] = f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT domain_node.id, project_node.id, FALSE
    FROM ({_MODEL_STORE_PROJECTS}) s
    JOIN domains d ON d.name = s.domain_name
    JOIN virtual_entities domain_node
      ON domain_node.entity_type = 'domain' AND domain_node.entity_id = d.id
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = s.project_id
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
"""

_ADD_DOMAIN_BINDINGS: Final[str] = f"""
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT project_node.id, domain_node.id, NULL
    FROM ({_MODEL_STORE_PROJECTS}) s
    JOIN domains d ON d.name = s.domain_name
    JOIN virtual_entities domain_node
      ON domain_node.entity_type = 'domain' AND domain_node.entity_id = d.id
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = s.project_id
    ON CONFLICT DO NOTHING
"""

_POLICY_PAIRS: Final[str] = f"""
    SELECT s.project_id AS project_id, p.uuid AS policy_id
    FROM ({_MODEL_STORE_PROJECTS}) s
    JOIN groups g ON g.id = s.project_id
    JOIN project_resource_policies p ON p.name = g.resource_policy
"""

_ADD_POLICY_NODES: Final[str] = f"""
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'project_resource_policy', pair.policy_id FROM ({_POLICY_PAIRS}) pair
    ON CONFLICT (entity_type, entity_id) DO NOTHING
"""

_ADD_POLICY_SHARES: Final[str] = f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT project_node.id, policy_node.id, TRUE
    FROM ({_POLICY_PAIRS}) pair
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = pair.project_id
    JOIN virtual_entities policy_node
      ON policy_node.entity_type = 'project_resource_policy'
     AND policy_node.entity_id = pair.policy_id
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
"""

_ADD_POLICY_CAPS: Final[str] = f"""
    INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
    SELECT em.id, :permission, TRUE
    FROM ({_POLICY_PAIRS}) pair
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = pair.project_id
    JOIN virtual_entities policy_node
      ON policy_node.entity_type = 'project_resource_policy'
     AND policy_node.entity_id = pair.policy_id
    JOIN entity_memberships em
      ON em.virtual_entity_id = project_node.id AND em.member_entity_id = policy_node.id
    ON CONFLICT (membership_id, permission) DO NOTHING
"""

# Every user of the domain is on the model-store project's roster, a share capped to
# read the way joining writes it.
_ROSTER_PAIRS: Final[str] = f"""
    SELECT s.project_id AS project_id, u.uuid AS user_id
    FROM ({_MODEL_STORE_PROJECTS}) s
    JOIN users u ON u.domain_name = s.domain_name
"""

_ADD_ROSTER_SHARES: Final[str] = f"""
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT project_node.id, user_node.id, TRUE
    FROM ({_ROSTER_PAIRS}) pair
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = pair.project_id
    JOIN virtual_entities user_node
      ON user_node.entity_type = 'user' AND user_node.entity_id = pair.user_id
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
"""

_ADD_ROSTER_CAPS: Final[str] = f"""
    INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
    SELECT em.id, :permission, TRUE
    FROM ({_ROSTER_PAIRS}) pair
    JOIN virtual_entities project_node
      ON project_node.entity_type = 'project' AND project_node.entity_id = pair.project_id
    JOIN virtual_entities user_node
      ON user_node.entity_type = 'user' AND user_node.entity_id = pair.user_id
    JOIN entity_memberships em
      ON em.virtual_entity_id = project_node.id AND em.member_entity_id = user_node.id
    ON CONFLICT (membership_id, permission) DO NOTHING
"""


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(_ADD_PROJECTS), {"policy_name": _POLICY_NAME})
    for statement in (_ADD_NODES, _ADD_SELF_EDGES, _ADD_SELF_BINDINGS):
        conn.execute(sa.text(statement))
    for statement in (_ADD_DOMAIN_OWNERSHIP, _ADD_DOMAIN_BINDINGS):
        conn.execute(sa.text(statement))
    conn.execute(sa.text(_ADD_POLICY_NODES))
    conn.execute(sa.text(_ADD_POLICY_SHARES))
    conn.execute(sa.text(_ADD_POLICY_CAPS), {"permission": _READ})
    conn.execute(sa.text(_ADD_ROSTER_SHARES))
    conn.execute(sa.text(_ADD_ROSTER_CAPS), {"permission": _READ})


def downgrade() -> None:
    # Nothing is removed: a project this revision registered cannot be told apart from
    # one a domain creation wrote, and removing it would take its model cards with it.
    pass
