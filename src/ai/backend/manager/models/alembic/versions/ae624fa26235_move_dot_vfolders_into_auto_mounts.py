"""Move dot-prefixed vfolders into vfolder auto-mounts

Every live vfolder whose name starts with a dot becomes an auto-mount of the user or the
project that owns it, with its graph node. A project's `.local` is not moved.

Revision ID: ae624fa26235
Revises: e7eaefa0781a
Create Date: 2026-11-25

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae624fa26235"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e7eaefa0781a"
branch_labels = None
depends_on = None

# The application generates v7 ids, so a v5 id of the vfolder marks a row written here.
_MOVED_AUTO_MOUNT_ID_NAMESPACE: Final[str] = "28784e2e-9917-4318-8e00-fb4fef108830"

_IS_MOVED_AUTO_MOUNT: Final[str] = (
    f"m.id = uuid_generate_v5('{_MOVED_AUTO_MOUNT_ID_NAMESPACE}', CAST(m.vfolder_id AS text))"
)

_MOVED_AUTO_MOUNT_NODES_AND_OWNER_NODES: Final[str] = f"""
    SELECT auto_mount_node.id AS auto_mount_node, owner_node.id AS owner_node
    FROM vfolder_auto_mounts m
    JOIN virtual_entities auto_mount_node
      ON auto_mount_node.entity_type = 'vfolder_auto_mount' AND auto_mount_node.entity_id = m.id
    JOIN virtual_entities owner_node
      ON (owner_node.entity_type, owner_node.entity_id)
         IN (('vfolder_auto_mount', m.id), (m.scope_type, m.scope_id))
    WHERE {_IS_MOVED_AUTO_MOUNT}
"""


def move_dot_vfolders(conn: sa.engine.Connection) -> None:
    # Of vfolders with one name in one scope, the oldest is inserted first and the rest conflict.
    conn.execute(
        sa.text(f"""
            INSERT INTO vfolder_auto_mounts
                (id, scope_type, scope_id, vfolder_id, mount_destination, subpath, mount_permission)
            SELECT
                uuid_generate_v5('{_MOVED_AUTO_MOUNT_ID_NAMESPACE}', CAST(v.id AS text)),
                scope_node.entity_type,
                scope_node.entity_id,
                v.id,
                CASE v.name
                    WHEN '.linuxbrew' THEN '/home/linuxbrew/.linuxbrew'
                    ELSE '/home/work/' || v.name
                END,
                '.',
                'rw'
            FROM vfolders v
            JOIN virtual_entities scope_node
              ON scope_node.entity_type
                 = CASE v.ownership_type WHEN 'user' THEN 'user' WHEN 'group' THEN 'project' END
             AND scope_node.entity_id
                 = CASE v.ownership_type WHEN 'user' THEN v."user" WHEN 'group' THEN v."group" END
            WHERE v.name LIKE '.%'
              AND v.status NOT IN (
                'delete-pending', 'delete-ongoing', 'delete-complete', 'delete-error'
              )
              AND NOT (v.ownership_type = 'group' AND v.name = '.local')
            ORDER BY v.created_at, v.id
            ON CONFLICT DO NOTHING
        """)
    )
    conn.execute(
        sa.text(f"""
            INSERT INTO virtual_entities (entity_type, entity_id)
            SELECT 'vfolder_auto_mount', m.id
            FROM vfolder_auto_mounts m
            WHERE {_IS_MOVED_AUTO_MOUNT}
            ON CONFLICT (entity_type, entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text(f"""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT n.owner_node, n.auto_mount_node, FALSE
            FROM ({_MOVED_AUTO_MOUNT_NODES_AND_OWNER_NODES}) n
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text(f"""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT n.auto_mount_node, n.owner_node, NULL
            FROM ({_MOVED_AUTO_MOUNT_NODES_AND_OWNER_NODES}) n
            ON CONFLICT (virtual_entity_id, scope_entity_id) DO NOTHING
        """)
    )


def remove_moved_auto_mounts(conn: sa.engine.Connection) -> None:
    # Removing a node removes its edges.
    conn.execute(
        sa.text(f"""
            DELETE FROM virtual_entities
            WHERE entity_type = 'vfolder_auto_mount'
              AND entity_id IN (
                SELECT m.id FROM vfolder_auto_mounts m WHERE {_IS_MOVED_AUTO_MOUNT}
              )
        """)
    )
    conn.execute(sa.text(f"DELETE FROM vfolder_auto_mounts m WHERE {_IS_MOVED_AUTO_MOUNT}"))


def upgrade() -> None:
    move_dot_vfolders(op.get_bind())


def downgrade() -> None:
    remove_moved_auto_mounts(op.get_bind())
