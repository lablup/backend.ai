"""migrate_container_registry_data_to_rbac

Revision ID: 2e42a745f939
Revises: 82e817b74ae4
Create Date: 2026-03-11 00:00:00.000000

"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "2e42a745f939"
down_revision = "82e817b74ae4"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
ENTITY_TYPE_CONTAINER_REGISTRY = "container_registry"
MEMBER_ROLE_SUFFIX = "member"
MEMBER_OPS = ["read"]
OWNER_OPS = sorted([
    "create",
    "read",
    "update",
    "soft-delete",
    "hard-delete",
    "grant:all",
    "grant:read",
    "grant:update",
    "grant:soft-delete",
    "grant:hard-delete",
])


def _add_entity_type_permissions(db_conn: Connection) -> None:
    """Add CONTAINER_REGISTRY entity-type permissions to all role+scope combinations.

    Uses a single set-based INSERT ... SELECT to derive CONTAINER_REGISTRY permissions
    for all role+scope combinations without application-side pagination.
    """
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
            "member_ops": MEMBER_OPS,
            "owner_ops": OWNER_OPS,
            "member_pattern": f"%{MEMBER_ROLE_SUFFIX}",
            "entity_type": ENTITY_TYPE_CONTAINER_REGISTRY,
        },
    )


def _associate_non_global_container_registries_to_scope(db_conn: Connection) -> None:
    """Associate non-global container registries to project scopes via junction table.

    Pages by registry IDs first, then JOINs to get all scope associations
    for each batch to avoid skipping rows in 1:N JOINs.
    """
    insert_query = sa.text("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        VALUES (:scope_type, :scope_id, :entity_type, :entity_id, :relation_type)
        ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
    """)

    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
        id_query = sa.text("""
            SELECT id FROM container_registries
            WHERE is_global = false AND id > :last_id
            ORDER BY id
            LIMIT :limit
        """)
        id_rows = db_conn.execute(id_query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not id_rows:
            break

        last_id = id_rows[-1].id
        entity_ids = [row.id for row in id_rows]

        assoc_query = sa.text("""
            SELECT cr.id AS entity_id, acrg.group_id::text AS scope_id
            FROM container_registries cr
            JOIN association_container_registries_groups acrg
                ON cr.id = acrg.registry_id
            WHERE cr.id = ANY(:entity_ids)
        """)
        rows = db_conn.execute(assoc_query, {"entity_ids": entity_ids}).all()

        values_list = [
            {
                "scope_type": "project",
                "scope_id": row.scope_id,
                "entity_type": ENTITY_TYPE_CONTAINER_REGISTRY,
                "entity_id": str(row.entity_id),
                "relation_type": "auto",
            }
            for row in rows
        ]

        if values_list:
            db_conn.execute(insert_query, values_list)


def _associate_global_container_registries_to_scope(db_conn: Connection) -> None:
    """Associate global container registries to ALL domain scopes.

    Global registries (is_global = true) are available to all domains.
    Pages by registry IDs first, then CROSS JOINs with domains to get
    all scope associations for each batch.
    """
    insert_query = sa.text("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        VALUES (:scope_type, :scope_id, :entity_type, :entity_id, :relation_type)
        ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
    """)

    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
        id_query = sa.text("""
            SELECT id FROM container_registries
            WHERE is_global = true AND id > :last_id
            ORDER BY id
            LIMIT :limit
        """)
        id_rows = db_conn.execute(id_query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not id_rows:
            break

        last_id = id_rows[-1].id
        entity_ids = [row.id for row in id_rows]

        assoc_query = sa.text("""
            SELECT cr.id AS entity_id, d.name AS scope_id
            FROM container_registries cr
            CROSS JOIN domains d
            WHERE cr.id = ANY(:entity_ids)
        """)
        rows = db_conn.execute(assoc_query, {"entity_ids": entity_ids}).all()

        values_list = [
            {
                "scope_type": "domain",
                "scope_id": row.scope_id,
                "entity_type": ENTITY_TYPE_CONTAINER_REGISTRY,
                "entity_id": str(row.entity_id),
                "relation_type": "auto",
            }
            for row in rows
        ]

        if values_list:
            db_conn.execute(insert_query, values_list)


def _remove_container_registry_edges(db_conn: Connection) -> None:
    """Remove all CONTAINER_REGISTRY AUTO edges from association_scopes_entities."""
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
            {
                "entity_type": ENTITY_TYPE_CONTAINER_REGISTRY,
                "relation_type": "auto",
                "limit": BATCH_SIZE,
            },
        )
        if result.rowcount == 0:
            break


def _remove_container_registry_permissions(db_conn: Connection) -> None:
    """Remove all CONTAINER_REGISTRY entity-type permissions."""
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
            {"entity_type": ENTITY_TYPE_CONTAINER_REGISTRY, "limit": BATCH_SIZE},
        )
        if result.rowcount == 0:
            break


def upgrade() -> None:
    conn = op.get_bind()
    _add_entity_type_permissions(conn)
    _associate_non_global_container_registries_to_scope(conn)
    _associate_global_container_registries_to_scope(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_container_registry_edges(conn)
    _remove_container_registry_permissions(conn)
