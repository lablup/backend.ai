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
    # Backfill only ``user``/``domain`` scopes (``public`` is superadmin-only, no role) and only
    # the write path (reads use the allow list, not RBAC). ``permission`` is the NOT NULL bitmask
    # from c6648c039bd4: bits are inlined as literals so this migration stays frozen against later
    # Permission enum changes, and grant operations have no bit (0).
    #
    # Sibling backfills (f1a2b3c4d5e6, 30c8308738ee, ...) select owner roles negatively, via
    # ``NOT (role_name LIKE '%member')``. That is unsafe here: role names carry no enforced
    # convention (``CreateRoleInput.name`` is a free string and the caller picks the scope), so a
    # custom read-only ``domain``-scoped role matches and would receive fragment ``hard-delete``
    # and ``grant:all`` over the whole domain. Select admins positively instead — by the
    # capability each domain admin role provably holds rather than by the shape of its name:
    #
    # * ``domain`` — the role must hold ``domain_admin_page`` at that same domain. Every domain
    #   admin role holds it under both naming schemes by the time this runs: 3b6297b1bd75 covers
    #   ``role_domain_%_admin``, f2b9a4c7e103/a3c1d8e5b294 cover ``domain-%-admin``, and all three
    #   are ancestors of this revision. ``domain_admin_page`` is absent from the frozen enum, so
    #   it is inlined as a literal, as those three migrations do.
    # * ``user`` — kept broad. A user-scope grant only ever reaches that user's own scope, and
    #   writing an own-scope fragment is deliberately not admin-only (see
    #   ``AppConfigScopeType.to_rbac_scope_type``).
    #
    # ``role_superadmin`` holds domain-scoped rows but no ``domain_admin_page``, so it drops out.
    # That is correct and matches 3b6297b1bd75: superadmin authority comes from the
    # ``user.is_superadmin`` short-circuit in the RBAC validators, never from these rows.
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
