"""migrate_notification_data_to_rbac

Revision ID: 013a6676866c
Revises: a5e87ed3b6d4
Create Date: 2025-12-23 16:55:10.781744

"""

from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.data.permission.id import ScopeType
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)

# revision identifiers, used by Alembic.
revision = "013a6676866c"
down_revision = "a5e87ed3b6d4"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_POSTFIX = "member"


@dataclass
class PermissionGroupInfo:
    id: UUID
    role_name: str


@dataclass
class PermissionInput:
    permission_group_id: UUID
    entity_type: str
    operation: str


def _get_permission_group_ids_with_role_name(
    db_conn: Connection,
    offset: int,
    limit: int,
) -> list[PermissionGroupInfo]:
    query = sa.text("""
        SELECT r.name AS role_name, pg.id AS permission_group_id
        FROM roles r
        JOIN permission_groups pg ON r.id = pg.role_id
        ORDER BY pg.id
        OFFSET :offset
        LIMIT :limit
    """)
    result = db_conn.execute(query, {"offset": offset, "limit": limit})
    rows = result.all()
    return [PermissionGroupInfo(row.permission_group_id, row.role_name) for row in rows]


def _add_entity_typed_permission_to_permission_groups(
    permission_group: PermissionGroupInfo,
    entity_type: EntityType,
) -> list[PermissionInput]:
    # Check if role name ends with "member"
    if permission_group.role_name.endswith(MEMBER_ROLE_POSTFIX):
        operations = OperationType.member_operations()
    else:
        operations = OperationType.owner_operations()

    return [
        PermissionInput(
            permission_group_id=permission_group.id,
            entity_type=entity_type.value,
            operation=operation.value,
        )
        for operation in operations
    ]


def _migrate_new_entity_type(db_conn: Connection) -> None:
    """Add NOTIFICATION_CHANNEL and NOTIFICATION_RULE entity type permissions to all permission groups."""
    offset = 0

    while True:
        perm_groups = _get_permission_group_ids_with_role_name(db_conn, offset, BATCH_SIZE)
        if not perm_groups:
            break

        offset += BATCH_SIZE
        inputs: list[PermissionInput] = []
        for perm_group in perm_groups:
            inputs.extend(
                _add_entity_typed_permission_to_permission_groups(
                    perm_group,
                    EntityType.NOTIFICATION_CHANNEL,
                )
            )
            inputs.extend(
                _add_entity_typed_permission_to_permission_groups(
                    perm_group,
                    EntityType.NOTIFICATION_RULE,
                )
            )

        if inputs:
            # Insert permissions using raw query
            values = ", ".join(
                f"('{input.permission_group_id}', '{input.entity_type}', '{input.operation}')"
                for input in inputs
            )
            query = sa.text(f"""
                INSERT INTO permissions (permission_group_id, entity_type, operation)
                VALUES {values}
                ON CONFLICT DO NOTHING
            """)
            db_conn.execute(query)


def _associate_notification_channels_to_scopes(db_conn: Connection) -> None:
    """Associate all notification channels to user scopes based on created_by."""
    offset = 0
    scope_type = ScopeType.USER.value
    entity_type = EntityType.NOTIFICATION_CHANNEL.value

    while True:
        query = sa.text("""
            SELECT id, created_by FROM notification_channels
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
            f"('{scope_type}', '{row.created_by}', '{entity_type}', '{row.id}')" for row in rows
        )

        insert_query = sa.text(f"""
            INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id)
            VALUES {values}
            ON CONFLICT DO NOTHING
        """)
        db_conn.execute(insert_query)


def _associate_notification_rules_to_scopes(db_conn: Connection) -> None:
    """Associate all notification rules to user scopes based on created_by."""
    offset = 0
    scope_type = ScopeType.USER.value
    entity_type = EntityType.NOTIFICATION_RULE.value

    while True:
        query = sa.text("""
            SELECT id, created_by FROM notification_rules
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
            f"('{scope_type}', '{row.created_by}', '{entity_type}', '{row.id}')" for row in rows
        )

        insert_query = sa.text(f"""
            INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id)
            VALUES {values}
            ON CONFLICT DO NOTHING
        """)
        db_conn.execute(insert_query)


def _remove_entity_from_scopes(db_conn: Connection, entity_type: EntityType) -> None:
    """Remove all entity-scope associations for a given entity type."""
    entity_type_value = entity_type.value

    while True:
        # Query records to delete
        query = sa.text("""
            SELECT id FROM association_scopes_entities
            WHERE entity_type = :entity_type
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"entity_type": entity_type_value, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        # Delete the queried records
        ids = ", ".join(f"'{row.id}'" for row in rows)
        delete_query = sa.text(f"""
            DELETE FROM association_scopes_entities
            WHERE id IN ({ids})
        """)
        db_conn.execute(delete_query)


def _remove_entity_type_permissions(db_conn: Connection, entity_type: EntityType) -> None:
    """Remove all entity type permissions for a given entity type."""
    entity_type_value = entity_type.value

    while True:
        # Query permission IDs to delete
        query = sa.text("""
            SELECT id FROM permissions
            WHERE entity_type = :entity_type
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"entity_type": entity_type_value, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        # Delete the queried permissions
        ids = ", ".join(f"'{row.id}'" for row in rows)
        delete_query = sa.text(f"""
            DELETE FROM permissions
            WHERE id IN ({ids})
        """)
        db_conn.execute(delete_query)


def upgrade() -> None:
    conn = op.get_bind()
    _migrate_new_entity_type(conn)
    _associate_notification_channels_to_scopes(conn)
    _associate_notification_rules_to_scopes(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_entity_from_scopes(conn, EntityType.NOTIFICATION_CHANNEL)
    _remove_entity_from_scopes(conn, EntityType.NOTIFICATION_RULE)
    _remove_entity_type_permissions(conn, EntityType.NOTIFICATION_CHANNEL)
    _remove_entity_type_permissions(conn, EntityType.NOTIFICATION_RULE)
