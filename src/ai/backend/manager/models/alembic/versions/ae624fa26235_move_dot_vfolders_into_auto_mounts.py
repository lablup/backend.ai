"""Move dot-prefixed vfolders into vfolder auto-mounts

Every live vfolder whose name starts with a dot becomes an auto-mount of the user or the
project that owns it, with its graph node. A project's `.local` is not moved.

Revision ID: ae624fa26235
Revises: e7eaefa0781a
Create Date: 2026-11-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae624fa26235"  # Part of: NEXT_RELEASE_VERSION
down_revision = "e7eaefa0781a"
branch_labels = None
depends_on = None


def move_dot_vfolders(conn: sa.engine.Connection) -> None:
    # An auto-mount a user registered stays: its vfolder or its destination conflicts.
    conn.execute(
        sa.text("""
            INSERT INTO vfolder_auto_mounts
                (scope_type, scope_id, vfolder_id, mount_destination, subpath, mount_permission)
            SELECT
                scope_node.entity_type, scope_node.entity_id, v.id, '/home/work/' || v.name, '.', 'rw'
            FROM vfolders v
            JOIN virtual_entities scope_node
              ON (v.ownership_type = 'user'
                  AND scope_node.entity_type = 'user' AND scope_node.entity_id = v."user")
              OR (v.ownership_type = 'group'
                  AND scope_node.entity_type = 'project' AND scope_node.entity_id = v."group")
            WHERE v.name LIKE '.%'
              AND NOT (v.ownership_type = 'group' AND v.name = '.local')
              AND v.status NOT IN (
                'delete-pending', 'delete-ongoing', 'delete-complete', 'delete-error'
              )
            ON CONFLICT DO NOTHING
        """)
    )
    # Give each auto-mount a node owning and governing itself, owned and governed by its scope.
    conn.execute(
        sa.text("""
            INSERT INTO virtual_entities (entity_type, entity_id)
            SELECT 'vfolder_auto_mount', id FROM vfolder_auto_mounts
            ON CONFLICT (entity_type, entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT id, id, FALSE FROM virtual_entities WHERE entity_type = 'vfolder_auto_mount'
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT id, id, NULL FROM virtual_entities WHERE entity_type = 'vfolder_auto_mount'
            ON CONFLICT (virtual_entity_id, scope_entity_id) DO NOTHING
        """)
    )
    auto_mount_and_scope_nodes = """
        SELECT auto_mount_node.id AS auto_mount_node, scope_node.id AS scope_node
        FROM vfolder_auto_mounts m
        JOIN virtual_entities auto_mount_node
          ON auto_mount_node.entity_type = 'vfolder_auto_mount' AND auto_mount_node.entity_id = m.id
        JOIN virtual_entities scope_node
          ON scope_node.entity_type = m.scope_type AND scope_node.entity_id = m.scope_id
    """
    conn.execute(
        sa.text(f"""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT n.scope_node, n.auto_mount_node, FALSE FROM ({auto_mount_and_scope_nodes}) n
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text(f"""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT n.auto_mount_node, n.scope_node, NULL FROM ({auto_mount_and_scope_nodes}) n
            ON CONFLICT (virtual_entity_id, scope_entity_id) DO NOTHING
        """)
    )


def remove_moved_auto_mounts(conn: sa.engine.Connection) -> None:
    # Removing a node removes its edges.
    conn.execute(
        sa.text("""
            WITH removed AS (
                DELETE FROM vfolder_auto_mounts m
                USING vfolders v
                WHERE v.id = m.vfolder_id
                  AND v.name LIKE '.%'
                  AND m.mount_destination = '/home/work/' || v.name
                RETURNING m.id
            )
            DELETE FROM virtual_entities
            WHERE entity_type = 'vfolder_auto_mount' AND entity_id IN (SELECT id FROM removed)
        """)
    )


def upgrade() -> None:
    move_dot_vfolders(op.get_bind())


def downgrade() -> None:
    remove_moved_auto_mounts(op.get_bind())
