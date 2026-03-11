"""migrate_keypair_data_to_rbac

Revision ID: 21159a293dfb
Revises: 359f0bbd936c
Create Date: 2026-03-11 20:44:01.574059

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)

# revision identifiers, used by Alembic.
revision = "21159a293dfb"
down_revision = "359f0bbd936c"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_SUFFIX = "member"


def _add_entity_type_permissions(db_conn: Connection) -> None:
    """Add KEYPAIR entity-type permissions to all role+scope combinations.

    Uses a single set-based INSERT ... SELECT to derive KEYPAIR permissions
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
            "entity_type": EntityType.KEYPAIR.value,
        },
    )


def _associate_keypair_to_scope(db_conn: Connection) -> None:
    """Associate keypair records to user scope using keyset pagination.

    Keypairs use access_key (String(20)) as PK instead of UUID id,
    so keyset pagination uses access_key with an initial empty string.
    """
    entity_type = EntityType.KEYPAIR.value
    relation_type = "auto"

    insert_query = sa.text("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        VALUES (:scope_type, :scope_id, :entity_type, :entity_id, :relation_type)
        ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
    """)

    last_id = ""
    while True:
        query = sa.text("""
            SELECT access_key AS id, "user"::text AS scope_id
            FROM keypairs
            WHERE access_key > :last_id
            ORDER BY access_key
            LIMIT :limit
        """)
        rows = db_conn.execute(query, {"last_id": last_id, "limit": BATCH_SIZE}).all()
        if not rows:
            break

        last_id = rows[-1].id
        values_list = [
            {
                "scope_type": "user",
                "scope_id": str(row.scope_id),
                "entity_type": entity_type,
                "entity_id": str(row.id),
                "relation_type": relation_type,
            }
            for row in rows
        ]

        if values_list:
            db_conn.execute(insert_query, values_list)


def _remove_keypair_edges(db_conn: Connection) -> None:
    """Remove all KEYPAIR AUTO edges from association_scopes_entities."""
    entity_type = EntityType.KEYPAIR.value
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


def _remove_keypair_permissions(db_conn: Connection) -> None:
    """Remove all KEYPAIR entity-type permissions."""
    entity_type = EntityType.KEYPAIR.value

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
    _associate_keypair_to_scope(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_keypair_edges(conn)
    _remove_keypair_permissions(conn)
