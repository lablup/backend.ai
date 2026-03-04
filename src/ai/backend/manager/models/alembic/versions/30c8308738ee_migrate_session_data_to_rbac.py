"""migrate_session_data_to_rbac

Revision ID: 30c8308738ee
Revises: 3f5c20f7bb07
Create Date: 2026-03-05 03:10:36.273207

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)

# revision identifiers, used by Alembic.
revision = "30c8308738ee"
down_revision = "3f5c20f7bb07"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_POSTFIX = "member"


def _add_entity_type_permissions(db_conn: Connection) -> None:
    """Add SESSION entity-type permissions to all role+scope combinations.

    This operation queries existing role+scope combinations from the permissions table
    and adds SESSION operations based on the role name.
    """
    offset = 0

    while True:
        # Get distinct role+scope combinations with role names
        query = sa.text("""
            SELECT DISTINCT p.role_id, r.name AS role_name, p.scope_type, p.scope_id
            FROM permissions p
            JOIN roles r ON p.role_id = r.id
            ORDER BY p.role_id, p.scope_type, p.scope_id
            OFFSET :offset
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"offset": offset, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        offset += BATCH_SIZE

        # Prepare permissions to insert
        values_list = []
        for row in rows:
            # Skip domain member roles (scope too broad for Session access)
            if row.scope_type == "domain" and row.role_name.endswith(MEMBER_ROLE_POSTFIX):
                continue

            # Determine operations based on role type
            if row.role_name.endswith(MEMBER_ROLE_POSTFIX):
                operations = OperationType.member_operations()
            else:
                operations = OperationType.owner_operations()

            # Add all operations for this role+scope
            for operation in operations:
                values_list.append(
                    f"('{row.role_id}', '{row.scope_type}', '{row.scope_id}', "
                    f"'{EntityType.SESSION.value}', '{operation.value}')"
                )

        if values_list:
            values = ", ".join(values_list)
            insert_query = sa.text(f"""
                INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
                VALUES {values}
                ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
            """)
            db_conn.execute(insert_query)


def _associate_sessions_to_scopes(db_conn: Connection) -> None:
    """Associate all sessions to their owner scopes (USER and PROJECT).

    Creates AUTO edges from:
    - User scope (user_uuid) → Session
    - Project scope (group_id) → Session

    Uses keyset pagination for scalability.
    """
    entity_type = EntityType.SESSION.value
    relation_type = "auto"

    # Process User scope edges
    last_id = "00000000-0000-0000-0000-000000000000"
    while True:
        query = sa.text("""
            SELECT id::text AS id, user_uuid::text AS user_uuid
            FROM sessions
            WHERE id::text > :last_id
            ORDER BY id
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        last_id = rows[-1].id

        # Prepare values for bulk insert
        values = ", ".join(
            f"('user', '{row.user_uuid}', '{entity_type}', '{row.id}', '{relation_type}')"
            for row in rows
        )

        insert_query = sa.text(f"""
            INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id, relation_type)
            VALUES {values}
            ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
        """)
        db_conn.execute(insert_query)

    # Process Project scope edges
    last_id = "00000000-0000-0000-0000-000000000000"
    while True:
        query = sa.text("""
            SELECT id::text AS id, group_id::text AS group_id
            FROM sessions
            WHERE id::text > :last_id
            ORDER BY id
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        last_id = rows[-1].id

        # Prepare values for bulk insert
        values = ", ".join(
            f"('project', '{row.group_id}', '{entity_type}', '{row.id}', '{relation_type}')"
            for row in rows
        )

        insert_query = sa.text(f"""
            INSERT INTO association_scopes_entities (scope_type, scope_id, entity_type, entity_id, relation_type)
            VALUES {values}
            ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
        """)
        db_conn.execute(insert_query)


def _remove_session_permissions(db_conn: Connection) -> None:
    """Remove all SESSION entity-type permissions."""
    entity_type = EntityType.SESSION.value

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


def _remove_session_edges(db_conn: Connection) -> None:
    """Remove all SESSION AUTO edges from association_scopes_entities."""
    entity_type = EntityType.SESSION.value

    while True:
        # Query association IDs to delete
        query = sa.text("""
            SELECT id FROM association_scopes_entities
            WHERE entity_type = :entity_type
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"entity_type": entity_type, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        # Delete the queried associations
        ids = ", ".join(f"'{row.id}'" for row in rows)
        delete_query = sa.text(f"""
            DELETE FROM association_scopes_entities
            WHERE id IN ({ids})
        """)
        db_conn.execute(delete_query)


def upgrade() -> None:
    conn = op.get_bind()
    _add_entity_type_permissions(conn)
    _associate_sessions_to_scopes(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_session_edges(conn)
    _remove_session_permissions(conn)
