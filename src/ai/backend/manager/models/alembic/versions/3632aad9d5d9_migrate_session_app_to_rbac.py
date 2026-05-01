"""migrate_session_app_to_rbac

Revision ID: 3632aad9d5d9
Revises: 6e5a7a62a687
Create Date: 2026-05-01 00:00:01.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "3632aad9d5d9"
down_revision = "6e5a7a62a687"
branch_labels = None
depends_on = None

# Part of: 26.5.0

# Constants
MEMBER_ROLE_SUFFIX = "member"
ENTITY_TYPE = "session:app"

# Org-hierarchy scope types. Other scope_type values in `permissions`
# (e.g. 'vfolder', 'model_deployment') are entity-as-scope grants for
# specific entities; they must be excluded from the entity-type seed.
ORG_SCOPE_TYPES = ["domain", "project", "user"]

# session:app is owner-only and read-only: app endpoints expose live
# state, so write/delete operations on the sub-entity itself are not
# meaningful.
OWNER_OPERATIONS = ["read"]


def _seed_entity_type_permissions(db_conn: Connection) -> None:
    """Seed `session:app` entity-type permissions for all non-member roles.

    For every distinct (role, scope) tuple already present in `permissions`,
    insert one `read` row, except for roles whose name ends with `member`
    (which intentionally have no access to internal session apps).

    Mirrors `30c8308738ee_migrate_session_data_to_rbac` and the
    accompanying `vfolder:data` migration.
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
            SELECT
                rs.role_id,
                rs.scope_type,
                rs.scope_id,
                unnest(CAST(:owner_ops AS text[])) AS operation
            FROM role_scopes rs
            WHERE rs.role_name NOT LIKE :member_pattern
              AND rs.scope_type = ANY(CAST(:org_scopes AS text[]))
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
            "owner_ops": OWNER_OPERATIONS,
            "member_pattern": f"%{MEMBER_ROLE_SUFFIX}",
            "org_scopes": ORG_SCOPE_TYPES,
            "entity_type": ENTITY_TYPE,
        },
    )


def upgrade() -> None:
    conn = op.get_bind()
    _seed_entity_type_permissions(conn)


def downgrade() -> None:
    # Intentionally a no-op. Once the runtime starts using `session:app`,
    # operators may grant/revoke additional permissions on this entity type.
    # A blanket DELETE WHERE entity_type='session:app' would erase those
    # operator-managed rows together with the seed, so this migration is
    # forward-only by design.
    pass
