"""migrate_vfolder_data_to_rbac

Revision ID: 6e5a7a62a687
Revises: 8c1f7d3a9e2b
Create Date: 2026-05-01 00:00:00.000000

"""

from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "6e5a7a62a687"
down_revision = "8c1f7d3a9e2b"
branch_labels = None
depends_on = None

# Part of: 26.5.0

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_SUFFIX = "member"
ENTITY_TYPE = "vfolder:data"
USER_SCOPE_TYPE = "user"
VFOLDER_SCOPE_TYPE = "vfolder"
REF_RELATION_TYPE = "ref"

# Org-hierarchy scope types. Other scope_type values in `permissions`
# (e.g. 'vfolder', 'model_deployment') are entity-as-scope grants for
# specific entities, not role-binding scopes — including them in the
# entity-type seed would over-grant per-entity invitees with full
# owner ops on `vfolder:data`.
ORG_SCOPE_TYPES = ["domain", "project", "user"]

# vfolder:data is owner-only: owner gets full CRUD on internal data,
# but soft-delete is intentionally omitted (no two-stage delete for data).
OWNER_OPERATIONS = ["create", "read", "update", "hard-delete"]

# Mount permission → vfolder:data operations.
# Aligned with vfolder:data owner ops (no soft-delete).
MOUNT_PERMISSION_TO_OPERATIONS: dict[str, list[str]] = {
    "ro": ["read"],
    "rw": ["read", "update"],
    "wd": ["read", "update", "hard-delete"],
}


def _seed_entity_type_permissions(db_conn: Connection) -> None:
    """Seed `vfolder:data` entity-type permissions for all non-member roles.

    For every distinct (role, scope) tuple already present in `permissions`,
    insert one row per owner operation, except:
    - roles whose name ends with `member` (project/user member roles get nothing)
    - domain-scoped roles whose name ends with `member` (already excluded above)

    This mirrors the pattern in `30c8308738ee_migrate_session_data_to_rbac`.
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


def _seed_invitation_permissions(db_conn: Connection) -> None:
    """Migrate vfolder_permissions invitations to vfolder:data permissions.

    Uses the modern entity-as-scope pattern (matches RBACGranter):
    for each (invited user, vfolder, mount permission), insert
    permissions(role_id=<invitee user-scope role>, scope_type='vfolder',
                scope_id=<vfolder_id>, entity_type='vfolder:data',
                operation=<each mapped op>).

    No `association_scopes_entities` rows are inserted: vfolder:data
    inherits scope from the parent vfolder edge created earlier, and the
    unique constraint `uq_scope_id_entity_id` (scope_type, scope_id,
    entity_id) would conflict with the existing vfolder edges anyway.
    """
    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
        # Resolve each invited user's user-scope ("system") role.
        # A user's system role is identified by holding any permission whose
        # scope is the user's own user-scope.
        query = sa.text("""
            SELECT
                vp.id AS row_id,
                vp.vfolder::text AS vfolder_id,
                vp.permission AS mount_permission,
                ur.role_id AS role_id
            FROM vfolder_permissions vp
            JOIN user_roles ur ON ur.user_id = vp."user"
            JOIN permissions p ON p.role_id = ur.role_id
            WHERE p.scope_type = :user_scope
              AND p.scope_id = vp."user"::text
              AND vp.id > :last_id
            GROUP BY vp.id, vp.vfolder, vp.permission, ur.role_id
            ORDER BY vp.id
            LIMIT :limit
        """)
        rows = db_conn.execute(
            query,
            {
                "user_scope": USER_SCOPE_TYPE,
                "last_id": last_id,
                "limit": BATCH_SIZE,
            },
        ).all()
        if not rows:
            break

        last_id = rows[-1].row_id

        values_list: list[dict[str, str]] = []
        for row in rows:
            ops = MOUNT_PERMISSION_TO_OPERATIONS.get(row.mount_permission)
            if not ops:
                # Unknown mount permission value — skip silently rather than
                # fail the migration.
                continue
            for operation in ops:
                values_list.append({
                    "role_id": str(row.role_id),
                    "scope_type": VFOLDER_SCOPE_TYPE,
                    "scope_id": row.vfolder_id,
                    "entity_type": ENTITY_TYPE,
                    "operation": operation,
                })

        if values_list:
            insert_query = sa.text("""
                INSERT INTO permissions
                    (role_id, scope_type, scope_id, entity_type, operation)
                VALUES
                    (:role_id, :scope_type, :scope_id, :entity_type, :operation)
                ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation)
                DO NOTHING
            """)
            db_conn.execute(insert_query, values_list)


def upgrade() -> None:
    conn = op.get_bind()
    _seed_entity_type_permissions(conn)
    _seed_invitation_permissions(conn)


def downgrade() -> None:
    # Intentionally a no-op. Once the runtime starts using `vfolder:data`,
    # operators may grant/revoke additional permissions on this entity type.
    # A blanket DELETE WHERE entity_type='vfolder:data' would erase those
    # operator-managed rows together with the seed, so this migration is
    # forward-only by design.
    pass
