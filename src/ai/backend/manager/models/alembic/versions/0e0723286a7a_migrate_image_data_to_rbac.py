"""migrate_image_data_to_rbac

Revision ID: 0e0723286a7a
Revises: 359f0bbd936c
Create Date: 2026-03-11 00:00:00.000000

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
revision = "0e0723286a7a"
down_revision = "359f0bbd936c"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_SUFFIX = "member"


def _add_entity_type_permissions(db_conn: Connection) -> None:
    """Add IMAGE entity-type permissions to all role+scope combinations.

    Uses a single set-based INSERT ... SELECT to derive IMAGE permissions
    for all role+scope combinations without application-side pagination.
    """
    # Precompute operation lists (sorted for deterministic ordering)
    member_ops = sorted(o.value for o in OperationType.member_operations())
    owner_ops = sorted(o.value for o in OperationType.owner_operations())

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
            "entity_type": EntityType.IMAGE.value,
        },
    )


def _associate_image_to_scope(db_conn: Connection) -> None:
    """Associate image records to project scope via container registry.

    Pages by image IDs first, then JOINs to get all scope associations
    for each batch to avoid skipping rows in 1:N JOINs.
    """
    entity_type = EntityType.IMAGE.value
    relation_type = "auto"
    scope_type = "project"

    insert_query = sa.text("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        VALUES (:scope_type, :scope_id, :entity_type, :entity_id, :relation_type)
        ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
    """)

    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
        id_query = sa.text("""
            SELECT id FROM images
            WHERE id > :last_id
            ORDER BY id
            LIMIT :limit
        """)
        id_rows = db_conn.execute(id_query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not id_rows:
            break

        last_id = id_rows[-1].id
        entity_ids = [row.id for row in id_rows]

        assoc_query = sa.text("""
            SELECT i.id AS entity_id, acrg.group_id AS scope_id
            FROM images i
            JOIN container_registries cr ON i.registry_id = cr.id
            JOIN association_container_registries_groups acrg ON cr.id = acrg.registry_id
            WHERE i.id = ANY(:entity_ids)
        """)
        rows = db_conn.execute(assoc_query, {"entity_ids": entity_ids}).all()

        values_list = [
            {
                "scope_type": scope_type,
                "scope_id": str(row.scope_id),
                "entity_type": entity_type,
                "entity_id": str(row.entity_id),
                "relation_type": relation_type,
            }
            for row in rows
        ]

        if values_list:
            db_conn.execute(insert_query, values_list)


def _remove_image_edges(db_conn: Connection) -> None:
    """Remove all IMAGE AUTO edges from association_scopes_entities."""
    entity_type = EntityType.IMAGE.value
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


def _remove_image_permissions(db_conn: Connection) -> None:
    """Remove all IMAGE entity-type permissions."""
    entity_type = EntityType.IMAGE.value

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


def upgrade() -> None:
    conn = op.get_bind()
    _add_entity_type_permissions(conn)
    _associate_image_to_scope(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_image_edges(conn)
    _remove_image_permissions(conn)
