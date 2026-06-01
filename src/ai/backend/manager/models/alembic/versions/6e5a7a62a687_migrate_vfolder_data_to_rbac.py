"""migrate_vfolder_data_to_rbac

Revision ID: 6e5a7a62a687
Revises: 46e007d9b237
Create Date: 2026-05-01 00:00:00.000000

"""

import logging
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "6e5a7a62a687"
down_revision = "46e007d9b237"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

# Part of: 26.5.0

# Constants
BATCH_SIZE = 1000
MEMBER_ROLE_PATTERN = "%member"
ENTITY_TYPE = "vfolder:data"
USER_SCOPE_TYPE = "user"
PROJECT_SCOPE_TYPE = "project"
VFOLDER_SCOPE_TYPE = "vfolder"

# vfolder:data is owner-only: only the literal owner gets full CRUD on
# internal data. Soft-delete is intentionally omitted because there is no
# two-stage delete for vfolder data.
OWNER_OPERATIONS = ["create", "read", "update", "hard-delete"]

# Mount permission → vfolder:data operations.
# Aligned with vfolder:data owner ops (no soft-delete).
MOUNT_PERMISSION_TO_OPERATIONS: dict[str, list[str]] = {
    "ro": ["read"],
    "rw": ["read", "update"],
    "wd": ["read", "update", "hard-delete"],
}


def _seed_user_owned_vfolder_grants(db_conn: Connection) -> None:
    """Per-entity grants for user-owned vfolders.

    For each vfolder owned by user U, grant U's user-scope ("system") role
    full vfolder:data owner operations on that specific vfolder via the
    entity-as-scope pattern. Grants land in the resolver's self-scope
    branch (matched on `scope_type='vfolder' AND scope_id=vfolder_id`) so
    they never leak upward via the scope-chain walker.
    """
    insert_query = sa.text("""
        WITH user_role_vfolders AS (
            SELECT DISTINCT
                ur.role_id,
                v.id::text AS vfolder_id
            FROM vfolders v
            JOIN user_roles ur ON ur.user_id = v."user"
            JOIN permissions p ON p.role_id = ur.role_id
            WHERE v.ownership_type = 'user'
              AND v."user" IS NOT NULL
              AND p.scope_type = :user_scope
              AND p.scope_id = v."user"::text
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT
            urv.role_id,
            :scope_type AS scope_type,
            urv.vfolder_id AS scope_id,
            :entity_type AS entity_type,
            unnest(CAST(:owner_ops AS text[])) AS operation
        FROM user_role_vfolders urv
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)
    db_conn.execute(
        insert_query,
        {
            "user_scope": USER_SCOPE_TYPE,
            "scope_type": VFOLDER_SCOPE_TYPE,
            "entity_type": ENTITY_TYPE,
            "owner_ops": OWNER_OPERATIONS,
        },
    )


def _seed_project_owned_vfolder_grants(db_conn: Connection) -> None:
    """Per-entity grants for project-owned vfolders.

    For each vfolder owned by project P, grant P's non-member roles
    (project owner / project admin) full vfolder:data owner operations
    on that specific vfolder. Same self-scope pattern — does not leak to
    user-owned vfolders within P via the walker.
    """
    insert_query = sa.text("""
        WITH project_role_vfolders AS (
            SELECT DISTINCT
                p.role_id,
                v.id::text AS vfolder_id
            FROM vfolders v
            JOIN permissions p
              ON p.scope_type = :project_scope
             AND p.scope_id = v."group"::text
            JOIN roles r ON r.id = p.role_id
            WHERE v.ownership_type = 'group'
              AND v."group" IS NOT NULL
              AND r.name NOT LIKE :member_pattern
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT
            prv.role_id,
            :scope_type AS scope_type,
            prv.vfolder_id AS scope_id,
            :entity_type AS entity_type,
            unnest(CAST(:owner_ops AS text[])) AS operation
        FROM project_role_vfolders prv
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)
    db_conn.execute(
        insert_query,
        {
            "project_scope": PROJECT_SCOPE_TYPE,
            "scope_type": VFOLDER_SCOPE_TYPE,
            "entity_type": ENTITY_TYPE,
            "owner_ops": OWNER_OPERATIONS,
            "member_pattern": MEMBER_ROLE_PATTERN,
        },
    )


def _seed_invitation_grants(db_conn: Connection) -> None:
    """Migrate vfolder_permissions invitations to per-entity vfolder:data grants.

    For each (invited user, vfolder, mount permission), grant the invitee's
    user-scope role the operations corresponding to their mount permission
    (`ro`→{read}, `rw`→{read,update}, `wd`→{read,update,hard-delete}).
    Same entity-as-scope pattern as the owner grants.
    """
    last_id = UUID("00000000-0000-0000-0000-000000000000")
    while True:
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
                logger.warning(
                    "Skipping vfolder_permissions row %s: unknown mount permission %r"
                    " (vfolder=%s, role=%s)",
                    row.row_id,
                    row.mount_permission,
                    row.vfolder_id,
                    row.role_id,
                )
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
    _seed_user_owned_vfolder_grants(conn)
    _seed_project_owned_vfolder_grants(conn)
    _seed_invitation_grants(conn)


def downgrade() -> None:
    # Intentionally a no-op. Once the runtime starts using `vfolder:data`,
    # operators may grant/revoke additional permissions on this entity type.
    # A blanket DELETE WHERE entity_type='vfolder:data' would erase those
    # operator-managed rows together with the seed, so this migration is
    # forward-only by design.
    pass
