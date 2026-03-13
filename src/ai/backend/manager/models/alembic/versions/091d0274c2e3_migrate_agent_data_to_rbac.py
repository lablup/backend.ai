"""migrate_agent_data_to_rbac

Revision ID: 091d0274c2e3
Revises: 359f0bbd936c
Create Date: 2026-03-11 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "091d0274c2e3"
down_revision = "359f0bbd936c"
branch_labels = None
depends_on = None

# Constants
BATCH_SIZE = 1000
ENTITY_TYPE_AGENT = "agent"
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
    """Add AGENT entity-type permissions to all role+scope combinations.

    Uses a single set-based INSERT ... SELECT to derive AGENT permissions
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
            "entity_type": ENTITY_TYPE_AGENT,
        },
    )


def _associate_agent_to_domain_scope(db_conn: Connection) -> None:
    """Associate agent records to domain scopes via scaling group junction table.

    Pages by agent IDs first, then JOINs to get all scope associations
    for each batch to avoid skipping rows in 1:N JOINs.
    """
    insert_query = sa.text("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        VALUES (:scope_type, :scope_id, :entity_type, :entity_id, :relation_type)
        ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
    """)

    last_id = ""
    while True:
        id_query = sa.text("""
            SELECT id FROM agents
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
            SELECT a.id AS entity_id, sfd.domain AS scope_id
            FROM agents a
            JOIN sgroups_for_domains sfd ON a.scaling_group = sfd.scaling_group
            WHERE a.id = ANY(:entity_ids)
        """)
        rows = db_conn.execute(assoc_query, {"entity_ids": entity_ids}).all()

        values_list = [
            {
                "scope_type": "domain",
                "scope_id": str(row.scope_id),
                "entity_type": ENTITY_TYPE_AGENT,
                "entity_id": str(row.entity_id),
                "relation_type": "auto",
            }
            for row in rows
        ]

        if values_list:
            db_conn.execute(insert_query, values_list)


def _associate_agent_to_project_scope(db_conn: Connection) -> None:
    """Associate agent records to project scopes via scaling group junction table.

    Pages by agent IDs first, then JOINs to get all scope associations
    for each batch to avoid skipping rows in 1:N JOINs.
    """
    insert_query = sa.text("""
        INSERT INTO association_scopes_entities
            (scope_type, scope_id, entity_type, entity_id, relation_type)
        VALUES (:scope_type, :scope_id, :entity_type, :entity_id, :relation_type)
        ON CONFLICT (scope_type, scope_id, entity_id) DO NOTHING
    """)

    last_id = ""
    while True:
        id_query = sa.text("""
            SELECT id FROM agents
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
            SELECT a.id AS entity_id, sfg."group"::text AS scope_id
            FROM agents a
            JOIN sgroups_for_groups sfg ON a.scaling_group = sfg.scaling_group
            WHERE a.id = ANY(:entity_ids)
        """)
        rows = db_conn.execute(assoc_query, {"entity_ids": entity_ids}).all()

        values_list = [
            {
                "scope_type": "project",
                "scope_id": str(row.scope_id),
                "entity_type": ENTITY_TYPE_AGENT,
                "entity_id": str(row.entity_id),
                "relation_type": "auto",
            }
            for row in rows
        ]

        if values_list:
            db_conn.execute(insert_query, values_list)


def _remove_agent_edges(db_conn: Connection) -> None:
    """Remove all AGENT AUTO edges from association_scopes_entities."""
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
            {"entity_type": ENTITY_TYPE_AGENT, "relation_type": "auto", "limit": BATCH_SIZE},
        )
        if result.rowcount == 0:
            break


def _remove_agent_permissions(db_conn: Connection) -> None:
    """Remove all AGENT entity-type permissions."""
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
            {"entity_type": ENTITY_TYPE_AGENT, "limit": BATCH_SIZE},
        )
        if result.rowcount == 0:
            break


def upgrade() -> None:
    conn = op.get_bind()
    _add_entity_type_permissions(conn)
    _associate_agent_to_domain_scope(conn)
    _associate_agent_to_project_scope(conn)


def downgrade() -> None:
    conn = op.get_bind()
    _remove_agent_edges(conn)
    _remove_agent_permissions(conn)
