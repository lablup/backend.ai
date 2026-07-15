"""add_app_config_fragment_permissions_to_rbac

Backfill ``APP_CONFIG_FRAGMENT`` permissions onto existing write-capable RBAC roles (a
user's own ``user``-scope role and ``domain`` admins) so they can exercise fragment writes
once RBAC enforcement is enabled (BEP-1052). New roles receive these permissions at role
creation; this migration only covers roles that predate the new entity type.

Only ``permissions`` rows are backfilled. The RBAC scope *associations*
(``association_scopes_entities``, which bind a fragment to its owning scope) are NOT
migrated: they are per-fragment and written at fragment-creation time, and this feature is
still unreleased, so no fragments — and therefore no associations — exist yet.

Revision ID: b3d9f7a2c184
Revises: c4e1a9b73f52
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
down_revision = "c4e1a9b73f52"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only ``user``/``domain`` scopes (``public`` is superadmin-only, no role) and only the write
    # path (reads use the allow list, not RBAC). Permission bits and ``domain_admin_page`` are
    # inlined as literals to stay frozen against later enum changes; grants have no bit (0).
    #
    # Domain admins are selected positively, by the ``domain_admin_page`` capability at the same
    # scope, not by the ``NOT (role_name LIKE '%member')`` filter sibling backfills use: role names
    # carry no enforced convention, so that filter would hand a custom read-only domain role
    # fragment ``hard-delete`` and ``grant:all``. ``user`` scope needs no such check — a user-scope
    # grant only ever reaches that user's own scope. ``role_superadmin`` holds no
    # ``domain_admin_page`` and drops out; its authority comes from the ``user.is_superadmin``
    # short-circuit in the RBAC validators, not these rows.
    db_conn = op.get_bind()
    db_conn.execute(
        sa.text("""
            WITH role_scopes AS (
                SELECT DISTINCT
                    p.role_id,
                    p.scope_type,
                    p.scope_id
                FROM permissions p
                WHERE p.scope_type IN ('user', 'domain')
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
                          AND admin_page.entity_type = 'domain_admin_page'
                          AND admin_page.scope_type = rs.scope_type
                          AND admin_page.scope_id = rs.scope_id
                   )
            )
            INSERT INTO permissions (
                role_id, scope_type, scope_id, entity_type, operation, permission
            )
            SELECT
                ro.role_id,
                ro.scope_type,
                ro.scope_id,
                :entity_type AS entity_type,
                ro.operation,
                CASE ro.operation
                    WHEN 'read' THEN 1
                    WHEN 'update' THEN 2
                    WHEN 'create' THEN 4
                    WHEN 'soft-delete' THEN 8
                    WHEN 'hard-delete' THEN 16
                    ELSE 0
                END AS permission
            FROM role_operations ro
            ON CONFLICT (role_id, scope_type, scope_id, entity_type, operation) DO NOTHING
        """),
        {
            "owner_ops": [op_type.value for op_type in OperationType.owner_operations()],
            "entity_type": EntityType.APP_CONFIG_FRAGMENT.value,
        },
    )


def downgrade() -> None:
    # No-op, following f2b9a4c7e103. Deleting by ``entity_type`` cannot distinguish the rows
    # this backfill inserted from the ones granted natively at role creation: current code
    # already writes APP_CONFIG_FRAGMENT permissions for every new role, because the entity
    # type is part of ``_resource_types()``. A blanket DELETE would therefore strip permissions
    # that roles created since this revision legitimately hold, and re-running ``upgrade`` would
    # not restore them for roles the backfill does not select. Leaving the rows in place is
    # safe — every row this migration writes is one role creation would have granted anyway.
    pass
