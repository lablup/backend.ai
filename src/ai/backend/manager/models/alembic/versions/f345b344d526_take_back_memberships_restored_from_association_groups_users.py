"""Take back the project memberships restored from association_groups_users

`f4a1c9d20b73` read `association_groups_users` as each project's roster before it was
fixed to read the graph. That table stopped being written when membership moved to the
scope association table, so a user taken off a project since then was put back on its
roster and given its auto_assign roles. Remove those edges and the roles granted with
them.

An edge that revision wrote is capped, names a pair the old table still holds, and was
written in the transaction that rewrote the preset roles' permission rows, so it shares
their creation time. A membership or grant written by the runtime does not.

Revision ID: f345b344d526
Revises: a7d0f5b3c841
Create Date: 2026-09-17

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f345b344d526"  # Part of: NEXT_RELEASE_VERSION
down_revision = "a7d0f5b3c841"
branch_labels = None
depends_on = None

_RESTORED: Final = """
    SELECT m.id AS membership_id, p.entity_id AS project_id, u.entity_id AS user_id,
           m.created_at
    FROM entity_memberships m
    JOIN virtual_entities p ON p.id = m.virtual_entity_id AND p.entity_type = 'project'
    JOIN virtual_entities u ON u.id = m.member_entity_id AND u.entity_type = 'user'
    JOIN association_groups_users agu
      ON agu.group_id = p.entity_id AND agu.user_id = u.entity_id
    WHERE m.capped
      AND EXISTS (
          SELECT 1 FROM permissions pm
          JOIN roles r ON r.id = pm.role_id
          WHERE r.role_preset_id IS NOT NULL AND pm.created_at = m.created_at
      )
"""

_REVOKE_ROLES: Final = sa.text(f"""
    DELETE FROM user_roles ur
    USING ({_RESTORED}) restored, roles r
    WHERE ur.user_id = restored.user_id
      AND ur.role_id = r.id
      AND r.scope_type = 'project'
      AND r.scope_id = restored.project_id
      AND ur.granted_at = restored.created_at
""")

_DROP_EDGES: Final = sa.text(f"""
    DELETE FROM entity_memberships
    WHERE id IN (SELECT membership_id FROM ({_RESTORED}) restored)
""")


def take_back_restored_memberships(conn: sa.Connection) -> None:
    conn.execute(_REVOKE_ROLES)
    conn.execute(_DROP_EDGES)


def upgrade() -> None:
    take_back_restored_memberships(op.get_bind())


def downgrade() -> None:
    # The removed rows were wrong; nothing is put back.
    pass
