"""add_app_config_fragment_permissions_to_rbac

Backfill ``APP_CONFIG_FRAGMENT`` permissions onto write-capable roles that predate the
entity type (BEP-1052); new roles receive them at role creation. Only ``permissions`` rows
are backfilled — the scope associations are written per-fragment at fragment-creation time,
and no fragments exist yet.

Revision ID: b3d9f7a2c184
Revises: c4e1a9b73f52
Create Date: 2026-07-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)

# revision identifiers, used by Alembic.
revision = "b3d9f7a2c184"
down_revision = "c4e1a9b73f52"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

DOMAIN_ADMIN_PAGE_ENTITY_TYPE = "domain_admin_page"
PROJECT_ADMIN_PAGE_ENTITY_TYPE = "project_admin_page"
APP_CONFIG_FRAGMENT_ENTITY_TYPE = EntityType.APP_CONFIG_FRAGMENT.value


def upgrade() -> None:
    db_conn = op.get_bind()
    _add_entity_type_permissions(db_conn)


def downgrade() -> None:
    # No-op, following f2b9a4c7e103: current code grants APP_CONFIG_FRAGMENT permissions to
    # every new role, so a DELETE by entity_type cannot tell this backfill's rows from those
    # and would strip permissions newer roles legitimately hold. Every row written here is one
    # role creation would have granted anyway, so leaving them in place is safe.
    pass


def _add_entity_type_permissions(db_conn: Connection) -> None:
    """Backfill APP_CONFIG_FRAGMENT owner permissions onto write-capable roles.

    - user scope → every role
    - domain/project scope → roles holding `domain_admin_page` / `project_admin_page`
    - members (read-only, served by the allow list), `public`, and `role_superadmin` are skipped

    Admins are matched by `*_admin_page` capability, not a `role_name LIKE '%member'` filter, since
    role names carry no enforced convention.
    """
    owner_ops = [op_type.value for op_type in OperationType.owner_operations()]

    # Bit values mirror ai.backend.common.data.permission.types.Permission (IntFlag), inlined as
    # literals to stay frozen against later enum changes — as in c6648c039bd4. Grant operations
    # (grant:*) have no dedicated bit and map to 0 (NONE).
    insert_query = sa.text("""
        WITH role_scopes AS (
            SELECT DISTINCT
                p.role_id,
                p.scope_type,
                p.scope_id
            FROM permissions p
            WHERE p.scope_type IN ('user', 'domain', 'project')
        ),
        role_operations AS (
            SELECT
                rs.role_id,
                rs.scope_type,
                rs.scope_id,
                unnest(CAST(:owner_ops AS text[])) AS operation
            FROM role_scopes rs
            WHERE rs.scope_type = 'user'
               OR EXISTS (
                    SELECT 1
                    FROM permissions admin_page
                    WHERE admin_page.role_id = rs.role_id
                      AND admin_page.entity_type = CASE rs.scope_type
                          WHEN 'domain' THEN :domain_admin_page_entity_type
                          WHEN 'project' THEN :project_admin_page_entity_type
                      END
                      AND admin_page.scope_type = rs.scope_type
                      AND admin_page.scope_id = rs.scope_id
               )
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation, permission)
        SELECT
            role_id,
            scope_type,
            scope_id,
            :entity_type AS entity_type,
            operation,
            CASE operation
                WHEN 'read' THEN 1
                WHEN 'update' THEN 2
                WHEN 'create' THEN 4
                WHEN 'soft-delete' THEN 8
                WHEN 'hard-delete' THEN 16
                ELSE 0
            END AS permission
        FROM role_operations
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)

    db_conn.execute(
        insert_query,
        {
            "owner_ops": owner_ops,
            "domain_admin_page_entity_type": DOMAIN_ADMIN_PAGE_ENTITY_TYPE,
            "project_admin_page_entity_type": PROJECT_ADMIN_PAGE_ENTITY_TYPE,
            "entity_type": APP_CONFIG_FRAGMENT_ENTITY_TYPE,
        },
    )
