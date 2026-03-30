"""migrate_vfolder_data_to_rbac

Revision ID: 2185ae0dd371
Revises: d86417a6bf7b
Create Date: 2026-01-07 11:28:24.914555

"""

from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)
from ai.backend.manager.models.rbac_models.migration.vfolder import (
    VFolderPermission,
    vfolder_mount_permission_to_operation,
)

# revision identifiers, used by Alembic.
revision = "2185ae0dd371"
down_revision = "d86417a6bf7b"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_POSTFIX = "member"


@dataclass
class PermissionGroupInfo:
    id: UUID
    role_name: str
    scope_type: str


def _get_permission_group_ids_with_role_name(
    db_conn: Connection,
    offset: int,
    limit: int,
) -> list[PermissionGroupInfo]:
    query = sa.text("""
        SELECT r.name AS role_name, pg.id AS permission_group_id, pg.scope_type
        FROM roles r
        JOIN permission_groups pg ON r.id = pg.role_id
        ORDER BY pg.id
        OFFSET :offset
        LIMIT :limit
    """)
    result = db_conn.execute(query, {"offset": offset, "limit": limit})
    rows = result.all()
    return [
        PermissionGroupInfo(row.permission_group_id, row.role_name, row.scope_type) for row in rows
    ]


def _add_entity_typed_permission_to_permission_groups(
    permission_group: PermissionGroupInfo,
) -> list[tuple[UUID, str, str]]:
    # Domain member should not have VFOLDER permissions
    # (domain scope is too broad for VFolder access)
    if permission_group.scope_type == "domain" and permission_group.role_name.endswith(
        MEMBER_ROLE_POSTFIX
    ):
        return []

    # Check if role name ends with "member"
    if permission_group.role_name.endswith(MEMBER_ROLE_POSTFIX):
        operations = OperationType.member_operations()
    else:
        operations = OperationType.owner_operations()

    return [
        (permission_group.id, EntityType.VFOLDER.value, operation.value) for operation in operations
    ]


def _migrate_new_entity_type(db_conn: Connection) -> None:
    """Add VFOLDER entity type permissions to all permission groups."""
    offset = 0

    while True:
        perm_groups = _get_permission_group_ids_with_role_name(db_conn, offset, BATCH_SIZE)
        if not perm_groups:
            break

        offset += BATCH_SIZE
        inputs: list[tuple[UUID, str, str]] = []
        for perm_group in perm_groups:
            inputs.extend(
                _add_entity_typed_permission_to_permission_groups(
                    perm_group,
                )
            )

        if inputs:
            # Insert permissions using raw query
            values = ", ".join(
                f"('{perm_id}', '{entity_type}', '{operation}')"
                for perm_id, entity_type, operation in inputs
            )
            query = sa.text(f"""
                INSERT INTO permissions (permission_group_id, entity_type, operation)
                VALUES {values}
                ON CONFLICT DO NOTHING
            """)
            db_conn.execute(query)


def _associate_entity_to_scopes(db_conn: Connection) -> None:
    """Associate all vfolders to their owner scopes (USER or PROJECT)."""
    entity_type = EntityType.VFOLDER.value

    # Process USER-owned vfolders
    offset = 0
    while True:
        query = sa.text("""
            SELECT id, "user"::text AS scope_id
            FROM vfolders
            WHERE ownership_type = 'user' AND "user" IS NOT NULL
            ORDER BY id
            OFFSET :offset
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"offset": offset, "limit": BATCH_SIZE}).all()
        if not rows:
            break
        offset += BATCH_SIZE

        # Prepare values for bulk insert
        values = ", ".join(
            f"('user', '{row.scope_id}', '{entity_type}', '{row.id}')" for row in rows
        )

        insert_query = sa.text(f"""
            INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id)
            VALUES {values}
            ON CONFLICT DO NOTHING
        """)
        db_conn.execute(insert_query)

    # Process GROUP-owned vfolders
    offset = 0
    while True:
        query = sa.text("""
            SELECT id, "group"::text AS scope_id
            FROM vfolders
            WHERE ownership_type = 'group' AND "group" IS NOT NULL
            ORDER BY id
            OFFSET :offset
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"offset": offset, "limit": BATCH_SIZE}).all()
        if not rows:
            break
        offset += BATCH_SIZE

        # Prepare values for bulk insert
        values = ", ".join(
            f"('project', '{row.scope_id}', '{entity_type}', '{row.id}')" for row in rows
        )

        insert_query = sa.text(f"""
            INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id)
            VALUES {values}
            ON CONFLICT DO NOTHING
        """)
        db_conn.execute(insert_query)


def _add_permission_groups_for_vfolder_invitations(db_conn: Connection) -> None:
    """
    Add permission_groups for invited users to access the VFolder owner's scope.

    When userA invites userB to a VFolder:
    - userB's system role gets a new permission_groups record
    - scope_type/scope_id points to userA's scope (the VFolder owner)
    """
    offset = 0

    while True:
        # Join vfolder_permissions with vfolders to get owner info,
        # and with user_roles + permission_groups to get the invited user's SYSTEM role only
        # System role is identified by: scope_type='user' AND scope_id=user_id
        query = sa.text("""
            SELECT DISTINCT
                ur.role_id,
                v.ownership_type,
                v."user" AS owner_user_id,
                v."group" AS owner_group_id
            FROM vfolder_permissions vp
            JOIN vfolders v ON vp.vfolder = v.id
            JOIN user_roles ur ON vp."user" = ur.user_id
            JOIN permission_groups pg ON ur.role_id = pg.role_id
            WHERE pg.scope_type = 'user' AND pg.scope_id = vp."user"::text
            ORDER BY ur.role_id
            OFFSET :offset
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"offset": offset, "limit": BATCH_SIZE}).all()
        if not rows:
            break
        offset += BATCH_SIZE

        # Prepare values for bulk insert
        values_list = []
        for row in rows:
            if row.ownership_type == "user" and row.owner_user_id is not None:
                scope_type = "user"
                scope_id = str(row.owner_user_id)
            elif row.ownership_type == "group" and row.owner_group_id is not None:
                scope_type = "project"
                scope_id = str(row.owner_group_id)
            else:
                continue

            values_list.append(f"('{row.role_id}', '{scope_type}', '{scope_id}')")

        if values_list:
            values = ", ".join(values_list)
            insert_query = sa.text(f"""
                INSERT INTO permission_groups (role_id, scope_type, scope_id)
                VALUES {values}
                ON CONFLICT DO NOTHING
            """)
            db_conn.execute(insert_query)


def _add_object_permissions_for_vfolder_invitations(db_conn: Connection) -> None:
    """
    Add object_permissions for specific VFolder access based on mount permission.

    Maps vfolder_permissions records to object_permissions:
    - role_id: invited user's SYSTEM role (user scope role)
    - entity_type: 'vfolder'
    - entity_id: specific VFolder ID
    - operation: based on mount permission (ro->READ, rw->READ+UPDATE, wd->READ+UPDATE+DELETE)
    """
    entity_type = EntityType.VFOLDER.value
    offset = 0

    while True:
        # Get the invited user's SYSTEM role only
        # System role is identified by: scope_type='user' AND scope_id=user_id
        query = sa.text("""
            SELECT
                ur.role_id,
                vp.vfolder::text AS vfolder_id,
                vp.permission AS mount_permission
            FROM vfolder_permissions vp
            JOIN user_roles ur ON vp."user" = ur.user_id
            JOIN permission_groups pg ON ur.role_id = pg.role_id
            WHERE pg.scope_type = 'user' AND pg.scope_id = vp."user"::text
            ORDER BY vp.id
            OFFSET :offset
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"offset": offset, "limit": BATCH_SIZE}).all()
        if not rows:
            break
        offset += BATCH_SIZE

        # Prepare values for bulk insert
        values_list = []
        for row in rows:
            try:
                mount_perm = VFolderPermission(row.mount_permission)
                operations = vfolder_mount_permission_to_operation[mount_perm]
            except (ValueError, KeyError):
                # Skip invalid permissions
                continue

            for operation in operations:
                values_list.append(
                    f"('{row.role_id}', '{entity_type}', '{row.vfolder_id}', '{operation.value}')"
                )

        if values_list:
            values = ", ".join(values_list)
            insert_query = sa.text(f"""
                INSERT INTO object_permissions (role_id, entity_type, entity_id, operation)
                VALUES {values}
                ON CONFLICT DO NOTHING
            """)
            db_conn.execute(insert_query)


def _remove_entity_from_scopes(db_conn: Connection) -> None:
    """Remove all vfolder-scope associations."""
    entity_type = EntityType.VFOLDER.value

    while True:
        # Query records to delete
        query = sa.text("""
            SELECT id FROM association_scopes_entities
            WHERE entity_type = :entity_type
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"entity_type": entity_type, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        # Delete the queried records
        ids = ", ".join(f"'{row.id}'" for row in rows)
        delete_query = sa.text(f"""
            DELETE FROM association_scopes_entities
            WHERE id IN ({ids})
        """)
        db_conn.execute(delete_query)


def _remove_entity_type_permissions(db_conn: Connection) -> None:
    """Remove all VFOLDER entity type permissions."""
    entity_type = EntityType.VFOLDER.value

    while True:
        # Query permission IDs to delete
        query = sa.text("""
            SELECT id FROM permissions
            WHERE entity_type = :entity_type
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"entity_type": entity_type, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        # Delete the queried permissions
        ids = ", ".join(f"'{row.id}'" for row in rows)
        delete_query = sa.text(f"""
            DELETE FROM permissions
            WHERE id IN ({ids})
        """)
        db_conn.execute(delete_query)


def _remove_object_permissions(db_conn: Connection) -> None:
    """Remove all VFOLDER object permissions."""
    entity_type = EntityType.VFOLDER.value

    while True:
        query = sa.text("""
            SELECT id FROM object_permissions
            WHERE entity_type = :entity_type
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"entity_type": entity_type, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        ids = ", ".join(f"'{row.id}'" for row in rows)
        delete_query = sa.text(f"""
            DELETE FROM object_permissions
            WHERE id IN ({ids})
        """)
        db_conn.execute(delete_query)


def upgrade() -> None:
    conn = op.get_bind()
    _migrate_new_entity_type(conn)
    _associate_entity_to_scopes(conn)
    _add_permission_groups_for_vfolder_invitations(conn)
    _add_object_permissions_for_vfolder_invitations(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_object_permissions(conn)
    _remove_entity_from_scopes(conn)
    _remove_entity_type_permissions(conn)
