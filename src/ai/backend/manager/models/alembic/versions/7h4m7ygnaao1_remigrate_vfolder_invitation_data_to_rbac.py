"""remigrate vfolder invitation data to rbac

Revision ID: 7h4m7ygnaao1
Revises: 3f5c20f7bb07
Create Date: 2026-03-05 00:00:00.000000

"""

import uuid

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
    last_id = uuid.UUID(int=0)

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
                ON CONFLICT (scope_type, scope_id, entity_id)
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
    last_id = uuid.UUID(int=0)

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


def upgrade() -> None:
    conn = op.get_bind()
    _upsert_ref_edges_for_invitations(conn)
    _insert_entity_as_scope_permissions_for_invitations(conn)


def downgrade() -> None:
    # Forward-only: the seeded rows are indistinguishable from ones granted
    # afterwards, so reverting them would erase operator-managed grants.
    pass
