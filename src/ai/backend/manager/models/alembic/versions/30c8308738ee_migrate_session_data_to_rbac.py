"""migrate_session_data_to_rbac

Revision ID: 30c8308738ee
Revises: 0e0723286a7a
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
down_revision = "0e0723286a7a"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_SUFFIX = "member"


def _add_entity_type_permissions(db_conn: Connection) -> None:
    """Add SESSION entity-type permissions to all role+scope combinations.

    Uses a single set-based INSERT ... SELECT to derive SESSION permissions
    for all role+scope combinations without application-side pagination.
    """
    # Precompute operation lists (sorted for deterministic ordering)
    member_ops = sorted(o.value for o in OperationType.member_operations())
    owner_ops = sorted(o.value for o in OperationType.owner_operations())

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
            "member_pattern": f"%{MEMBER_ROLE_SUFFIX}",
            "entity_type": EntityType.SESSION.value,
        },
    )


def _associate_sessions_to_scope(
    db_conn: Connection,
    scope_type: str,
    scope_id_column: str,
) -> None:
    """Associate sessions to a given scope type using keyset pagination.

    Creates AUTO edges from the specified scope to each session.
    """
    entity_type = EntityType.SESSION.value
    relation_type = "auto"

    insert_query = sa.text("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        VALUES (:scope_type, :scope_id, :entity_type, :entity_id, :relation_type)
        ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
    """)

    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
        query = sa.text(f"""
            SELECT id, {scope_id_column} AS scope_id
            FROM sessions
            WHERE id > :last_id
            ORDER BY id
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        last_id = rows[-1].id

        values_list = [
            {
                "scope_type": scope_type,
                "scope_id": str(row.scope_id),
                "entity_type": entity_type,
                "entity_id": str(row.id),
                "relation_type": relation_type,
            }
            for row in rows
        ]

        if values_list:
            db_conn.execute(insert_query, values_list)


def _remove_session_permissions(db_conn: Connection) -> None:
    """Remove all SESSION entity-type permissions."""
    entity_type = EntityType.SESSION.value

    while True:
        delete_query = sa.text("""
            DELETE FROM permissions
            WHERE id IN (
                SELECT id FROM permissions
                WHERE entity_type = :entity_type
                LIMIT :limit
            )
        """)
        result = db_conn.execute(
            delete_query,
            {"entity_type": entity_type, "limit": BATCH_SIZE},
        )
        if result.rowcount == 0:
            break


def _remove_session_edges(db_conn: Connection) -> None:
    """Remove all SESSION AUTO edges from association_scopes_entities."""
    entity_type = EntityType.SESSION.value
    relation_type = "auto"

    while True:
        delete_query = sa.text("""
            DELETE FROM association_scopes_entities
            WHERE id IN (
                SELECT id FROM association_scopes_entities
                WHERE entity_type = :entity_type
                  AND relation_type = :relation_type
                LIMIT :limit
            )
        """)
        result = db_conn.execute(
            delete_query,
            {"entity_type": entity_type, "relation_type": relation_type, "limit": BATCH_SIZE},
        )
        if result.rowcount == 0:
            break


def upgrade() -> None:
    conn = op.get_bind()
    _add_entity_type_permissions(conn)
    _associate_sessions_to_scope(conn, "user", "user_uuid")
    _associate_sessions_to_scope(conn, "project", "group_id")


def downgrade() -> None:
    conn = op.get_bind()
    _remove_session_edges(conn)
    _remove_session_permissions(conn)
