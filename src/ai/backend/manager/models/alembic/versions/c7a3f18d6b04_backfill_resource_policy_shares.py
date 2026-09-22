"""Backfill the share a scope holds on the policy it is subject to

The revision before this granted the seed roles read on their own policy, and the write
path lends the policy as a capped share wherever an assignment changes. A scope assigned
its policy before either landed holds no share, so the read still answers nothing until
something reassigns the policy. Lend each scope the policy it is subject to now.

Revision ID: c7a3f18d6b04
Revises: b8e0c1f4a276
Create Date: 2026-09-22

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7a3f18d6b04"  # Part of: NEXT_RELEASE_VERSION
down_revision = "b8e0c1f4a276"
branch_labels = None
depends_on = None

_READ: Final[int] = 1

# The scope a policy applies to, paired with the policy it is subject to. A keypair is a
# field of the user, so the user is the scope; the key read is the one the user
# authorizes with, chosen the way the write path chooses it.
_PAIRS: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "user",
        "user_resource_policy",
        """
        SELECT u.uuid AS scope_id, p.uuid AS policy_id
        FROM users u
        JOIN user_resource_policies p ON p.name = u.resource_policy
        """,
    ),
    (
        "user",
        "keypair_resource_policy",
        """
        SELECT u.uuid AS scope_id, p.uuid AS policy_id
        FROM users u
        JOIN LATERAL (
            SELECT k.resource_policy
            FROM keypairs k
            WHERE k.user = u.uuid AND k.is_active IS TRUE
            ORDER BY k.is_default DESC, k.created_at ASC, k.access_key ASC
            LIMIT 1
        ) key ON TRUE
        JOIN keypair_resource_policies p ON p.name = key.resource_policy
        """,
    ),
    (
        "project",
        "project_resource_policy",
        """
        SELECT g.id AS scope_id, p.uuid AS policy_id
        FROM groups g
        JOIN project_resource_policies p ON p.name = g.resource_policy
        """,
    ),
)

_ADD_NODES: Final[str] = """
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT :entity_type, s.policy_id FROM ({source}) s
    ON CONFLICT (entity_type, entity_id) DO NOTHING
"""

_ADD_SHARES: Final[str] = """
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT scope_node.id, policy_node.id, TRUE
    FROM ({source}) s
    JOIN virtual_entities scope_node
      ON scope_node.entity_type = :scope_type AND scope_node.entity_id = s.scope_id
    JOIN virtual_entities policy_node
      ON policy_node.entity_type = :entity_type AND policy_node.entity_id = s.policy_id
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
"""

_ADD_CAPS: Final[str] = """
    INSERT INTO entity_membership_caps (membership_id, permission, all_fields)
    SELECT em.id, :permission, TRUE
    FROM ({source}) s
    JOIN virtual_entities scope_node
      ON scope_node.entity_type = :scope_type AND scope_node.entity_id = s.scope_id
    JOIN virtual_entities policy_node
      ON policy_node.entity_type = :entity_type AND policy_node.entity_id = s.policy_id
    JOIN entity_memberships em
      ON em.virtual_entity_id = scope_node.id AND em.member_entity_id = policy_node.id
    ON CONFLICT (membership_id, permission) DO NOTHING
"""

_DROP_SHARES: Final[str] = """
    DELETE FROM entity_memberships em
    USING ({source}) s, virtual_entities scope_node, virtual_entities policy_node
    WHERE scope_node.entity_type = :scope_type AND scope_node.entity_id = s.scope_id
      AND policy_node.entity_type = :entity_type AND policy_node.entity_id = s.policy_id
      AND em.virtual_entity_id = scope_node.id
      AND em.member_entity_id = policy_node.id
      AND em.capped IS TRUE
"""


def upgrade() -> None:
    conn = op.get_bind()
    for scope_type, entity_type, source in _PAIRS:
        params = {"scope_type": scope_type, "entity_type": entity_type}
        conn.execute(
            sa.text(_ADD_NODES.format(source=source)),
            {"entity_type": entity_type},
        )
        conn.execute(sa.text(_ADD_SHARES.format(source=source)), params)
        conn.execute(
            sa.text(_ADD_CAPS.format(source=source)),
            {**params, "permission": _READ},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for scope_type, entity_type, source in _PAIRS:
        conn.execute(
            sa.text(_DROP_SHARES.format(source=source)),
            {"scope_type": scope_type, "entity_type": entity_type},
        )
