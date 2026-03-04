"""migrate_session_data_to_rbac

Revision ID: 30c8308738ee
Revises: 3f5c20f7bb07
Create Date: 2026-03-05 03:10:36.273207

"""

from uuid import UUID

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

    Uses a single set-based INSERT ... SELECT to derive SESSION permissions
    for all role+scope combinations without application-side pagination.
    """
    # Precompute operation lists
    member_ops = [op.value for op in OperationType.member_operations()]
    owner_ops = [op.value for op in OperationType.owner_operations()]

    # Insert SESSION permissions in a single set-based query
    #
    # Rules:
    # - Skip roles where scope_type == 'domain' and role_name ends with 'member'
    # - For non-domain member roles, use member_ops (READ only)
    # - For all other roles (owner/admin), use owner_ops (all operations)
    insert_query = sa.text("""
        WITH role_scopes AS (
            SELECT DISTINCT
                p.role_id,
                r.name AS role_name,
                p.scope_type,
                p.scope_id
            FROM permissions p
            JOIN roles r ON p.role_id = r.id
        ),
        role_operations AS (
            -- Member operations for non-domain member roles
            SELECT
                rs.role_id,
                rs.scope_type,
                rs.scope_id,
                unnest(CAST(:member_ops AS text[])) AS operation
            FROM role_scopes rs
            WHERE rs.scope_type != 'domain'
              AND rs.role_name LIKE :member_pattern

            UNION ALL

            -- Owner operations for non-member roles
            SELECT
                rs.role_id,
                rs.scope_type,
                rs.scope_id,
                unnest(CAST(:owner_ops AS text[])) AS operation
            FROM role_scopes rs
            WHERE NOT (rs.role_name LIKE :member_pattern)
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT
            role_id,
            scope_type,
            scope_id,
            :entity_type AS entity_type,
            operation
        FROM role_operations
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)

    db_conn.execute(
        insert_query,
        {
            "member_ops": member_ops,
            "owner_ops": owner_ops,
            "member_pattern": f"%{MEMBER_ROLE_POSTFIX}",
            "entity_type": EntityType.SESSION.value,
        },
    )


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
    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
        query = sa.text("""
            SELECT id, user_uuid
            FROM sessions
            WHERE id > :last_id
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
    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
        query = sa.text("""
            SELECT id, group_id
            FROM sessions
            WHERE id > :last_id
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
