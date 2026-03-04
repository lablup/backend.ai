"""remigrate vfolder invitation data to rbac

Revision ID: 7h4m7ygnaao1
Revises: 3f5c20f7bb07
Create Date: 2026-03-05 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
)
from ai.backend.manager.models.rbac_models.migration.vfolder import (
    VFolderPermission,
    vfolder_mount_permission_to_operation,
)

# revision identifiers, used by Alembic.
revision = "7h4m7ygnaao1"
down_revision = "3f5c20f7bb07"
branch_labels = None
depends_on = "ccf8ae5c90fe"

# Constants
BATCH_SIZE = 1000


def _upsert_ref_edges_for_invitations(db_conn: Connection) -> None:
    """
    Upsert REF edges for VFolder invitations in association_scopes_entities.

    For each vfolder_permissions row, create/update an edge with relation_type='ref'.
    This handles:
    - New entries: inserts with relation_type='ref'
    - Existing AUTO entries (from old migration): corrects to 'ref'
    - Existing REF entries (from runtime): no-op
    """
    entity_type = EntityType.VFOLDER.value
    last_id = 0

    while True:
        # Query vfolder_permissions in batches using keyset pagination
        query = sa.text("""
            SELECT
                vp."user"::text AS user_id,
                vp.vfolder::text AS vfolder_id,
                vp.id AS id
            FROM vfolder_permissions vp
            WHERE vp.id > :last_id
            ORDER BY vp.id
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not rows:
            break
        last_id = rows[-1].id

        # Build upsert query for batch
        for row in rows:
            upsert_query = sa.text("""
                INSERT INTO association_scopes_entities
                    (scope_type, scope_id, entity_type, entity_id, relation_type)
                VALUES ('user', :user_id, :entity_type, :vfolder_id, 'ref')
                ON CONFLICT (scope_type, scope_id, entity_type, entity_id)
                    DO UPDATE SET relation_type = 'ref'
            """)
            db_conn.execute(
                upsert_query,
                {
                    "user_id": row.user_id,
                    "entity_type": entity_type,
                    "vfolder_id": row.vfolder_id,
                },
            )


def _insert_entity_as_scope_permissions_for_invitations(db_conn: Connection) -> None:
    """
    Insert entity-as-scope permissions for VFolder invitations.

    For each vfolder_permissions row:
    1. Get the user's role_id from user_roles
    2. Map mount permission to operations
    3. Insert into permissions with scope_type='vfolder', scope_id=vfolder_id
    """
    entity_type = EntityType.VFOLDER.value
    last_id = 0

    while True:
        # Query vfolder_permissions with role_id using keyset pagination
        query = sa.text("""
            SELECT
                ur.role_id,
                vp.vfolder::text AS vfolder_id,
                vp.permission AS mount_permission,
                vp.id AS id
            FROM vfolder_permissions vp
            JOIN user_roles ur ON vp."user" = ur.user_id
            WHERE vp.id > :last_id
            ORDER BY vp.id
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not rows:
            break
        last_id = rows[-1].id

        # Process each row and insert permissions
        for row in rows:
            try:
                mount_perm = VFolderPermission(row.mount_permission)
                operations = vfolder_mount_permission_to_operation[mount_perm]
            except (ValueError, KeyError):
                # Skip invalid permissions
                continue

            for operation in operations:
                insert_query = sa.text("""
                    INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
                    VALUES (:role_id, 'vfolder', :vfolder_id, :entity_type, :operation)
                    ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
                """)
                db_conn.execute(
                    insert_query,
                    {
                        "role_id": str(row.role_id),
                        "vfolder_id": row.vfolder_id,
                        "entity_type": entity_type,
                        "operation": operation.value,
                    },
                )


def _revert_ref_edges_to_auto(db_conn: Connection) -> None:
    """
    Revert REF edges back to AUTO (restore old migration's state).

    Only edges derived from vfolder invitations are reverted:
    - entity_type = VFOLDER
    - scope_type = 'user'
    - (scope_id, entity_id) pairs present in vfolder_permissions (user_id, vfolder_id)

    This is a batched operation to handle large datasets.
    """
    entity_type = EntityType.VFOLDER.value
    last_id = 0

    while True:
        # Query invitation-derived REF edges in batches using keyset pagination
        query = sa.text("""
            SELECT ase.id
            FROM association_scopes_entities AS ase
            JOIN vfolder_permissions AS vp
              ON ase.scope_type = 'user'
             AND ase.entity_type = :entity_type
             AND ase.scope_id = vp."user"::text
             AND ase.entity_id = vp.vfolder::text
            WHERE ase.relation_type = 'ref'
              AND ase.id > :last_id
            ORDER BY ase.id
            LIMIT :limit
        """)
        rows = db_conn.execute(
            query,
            {"entity_type": entity_type, "last_id": last_id, "limit": BATCH_SIZE},
        ).all()
        if not rows:
            break
        last_id = rows[-1].id

        # Update the queried records using parameterized query
        for row in rows:
            update_query = sa.text("""
                UPDATE association_scopes_entities
                SET relation_type = 'auto'
                WHERE id = :id
            """)
            db_conn.execute(update_query, {"id": str(row.id)})


def _remove_entity_as_scope_permissions(db_conn: Connection) -> None:
    """
    Remove entity-as-scope permissions for VFolder invitations.

    This removes only those permissions that were introduced by this migration,
    i.e., permissions derived from vfolder invitation records in vfolder_permissions
    using the same mount-permission-to-operation mapping as in the upgrade step.

    Batched operation to handle large datasets.
    """
    entity_type = EntityType.VFOLDER.value
    last_id = 0

    while True:
        # Fetch a batch of vfolder invitation records from vfolder_permissions
        vfolder_query = sa.text("""
            SELECT
                vp.id,
                ur.role_id,
                vp.vfolder::text AS vfolder_id,
                vp.permission AS mount_permission
            FROM vfolder_permissions vp
            JOIN user_roles ur ON vp."user" = ur.user_id
            WHERE vp.id > :last_id
            ORDER BY vp.id
            LIMIT :limit
        """)
        vfolder_rows = db_conn.execute(
            vfolder_query,
            {"last_id": last_id, "limit": BATCH_SIZE},
        ).all()

        if not vfolder_rows:
            break

        for row in vfolder_rows:
            try:
                # Map mount_permission to one or more RBAC operations,
                # mirroring the logic used during upgrade
                mount_perm = VFolderPermission(row.mount_permission)
                operations = vfolder_mount_permission_to_operation[mount_perm]
            except (ValueError, KeyError):
                # Skip invalid permissions
                continue

            for operation in operations:
                delete_query = sa.text("""
                    DELETE FROM permissions
                    WHERE role_id = :role_id
                      AND scope_type = 'vfolder'
                      AND scope_id = :scope_id
                      AND entity_type = :entity_type
                      AND operation = :operation
                """)
                db_conn.execute(
                    delete_query,
                    {
                        "role_id": str(row.role_id),
                        "scope_id": row.vfolder_id,
                        "entity_type": entity_type,
                        "operation": operation.value,
                    },
                )

        # Advance pagination cursor using the highest processed vfolder_permissions.id
        last_id = vfolder_rows[-1].id


def upgrade() -> None:
    conn = op.get_bind()
    _upsert_ref_edges_for_invitations(conn)
    _insert_entity_as_scope_permissions_for_invitations(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_entity_as_scope_permissions(conn)
    _revert_ref_edges_to_auto(conn)
