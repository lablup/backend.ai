"""add_app_config_fragment_permissions_to_rbac

Backfill ``APP_CONFIG_FRAGMENT`` permissions onto existing RBAC roles so that already
provisioned user / domain / project roles can exercise fragment writes once RBAC
enforcement is enabled (BEP-1052). New roles receive these permissions at creation via the
runtime allow list; this migration covers roles that predate the allow-list change.

Revision ID: b3d9f7a2c184
Revises: a3c1d8e5b294
Create Date: 2026-07-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)

# revision identifiers, used by Alembic.
revision = "b3d9f7a2c184"
down_revision = "a3c1d8e5b294"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

MEMBER_ROLE_SUFFIX = "member"
APP_CONFIG_FRAGMENT_ENTITY_TYPE = EntityType.APP_CONFIG_FRAGMENT.value


def upgrade() -> None:
    db_conn = op.get_bind()
    _add_app_config_fragment_permissions(db_conn)


def downgrade() -> None:
    db_conn = op.get_bind()
    db_conn.execute(
        sa.text("DELETE FROM permissions WHERE entity_type = :entity_type"),
        {"entity_type": APP_CONFIG_FRAGMENT_ENTITY_TYPE},
    )


def _add_app_config_fragment_permissions(db_conn: sa.engine.Connection) -> None:
    """Backfill APP_CONFIG_FRAGMENT write permissions onto existing write-capable roles.

    A fragment lives only at ``user`` or ``domain`` scope (``public`` is global →
    superadmin-only, no role), so only those scopes are touched — a permission at any
    other scope (``project`` etc.) could never match a real fragment. Reads go through the
    allow list, not RBAC, so only the write path needs backfilling: grant the full
    operation set to the write-capable roles, i.e. a user's own ``user``-scope role and
    ``domain`` admins. Member roles are excluded (they do not write fragments).
    """
    owner_ops = [op_type.value for op_type in OperationType.owner_operations()]

    insert_query = sa.text("""
        WITH role_scopes AS (
            SELECT DISTINCT
                p.role_id,
                r.name AS role_name,
                p.scope_type,
                p.scope_id
            FROM permissions p
            JOIN roles r ON p.role_id = r.id
            WHERE p.scope_type IN ('user', 'domain')
        )
        INSERT INTO permissions (role_id, scope_type, scope_id, entity_type, operation)
        SELECT
            rs.role_id,
            rs.scope_type,
            rs.scope_id,
            :entity_type AS entity_type,
            unnest(CAST(:owner_ops AS text[])) AS operation
        FROM role_scopes rs
        WHERE NOT (rs.role_name LIKE :member_pattern)
        ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
    """)

    db_conn.execute(
        insert_query,
        {
            "owner_ops": owner_ops,
            "member_pattern": f"%{MEMBER_ROLE_SUFFIX}",
            "entity_type": APP_CONFIG_FRAGMENT_ENTITY_TYPE,
        },
    )
