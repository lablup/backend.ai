"""backfill project member roles and promote legacy custom sources to system

Normalizes the project member role across all projects so that every project
has exactly one SYSTEM-sourced member role at its scope. This fixes two
historical gaps:

1. Projects created after migration 430b1631804d had no member role at all,
   because the runtime create path only created a project admin role. For
   these, a new SYSTEM-sourced member role is created together with its
   scope binding and member permissions.
2. Projects created before 430b1631804d received a member role from that
   migration, but with source=CUSTOM. For these, the existing role row is
   promoted to source=SYSTEM in place; no new role is created and existing
   permissions / user-role mappings are preserved.

Runtime creation of the member role is introduced alongside this migration in
GroupDBSource.create(), so new projects created after this migration lands
will already have both roles and the migration will be a no-op for them.

Revision ID: e3fb172166dc
Revises: d8e4f2a1b3c7
Create Date: 2026-04-15

"""

import uuid
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.models.base import GUID, IDColumn
from ai.backend.manager.models.rbac_models.migration.enums import (
    RoleSource,
    RoleStatus,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
    get_roles_table,
    mapper_registry,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_skip_on_conflict,
    query_role_rows_by_name,
)

# revision identifiers, used by Alembic.
revision = "e3fb172166dc"
down_revision = "d8e4f2a1b3c7"
# Part of: 26.5.0
branch_labels = None
depends_on = None


# Snapshot of MEMBER_ACCESSIBLE_ENTITY_TYPES_IN_PROJECT at the time of writing.
# Kept inline so that runtime enum changes do not retroactively alter the set
# of permissions granted by this migration.
_MEMBER_ACCESSIBLE_ENTITY_TYPES: tuple[str, ...] = (
    "user",
    "vfolder",
    "image",
    "session",
    "artifact",
    "artifact_registry",
    "app_config",
    "notification_channel",
    "notification_rule",
    "model_deployment",
    "model_card",
)

# Snapshot of OperationType.member_operations() — member roles only grant READ.
_MEMBER_OPERATIONS: tuple[str, ...] = ("read",)


def _get_groups_table() -> sa.Table:
    return sa.Table(
        "groups",
        mapper_registry.metadata,
        IDColumn(),
        extend_existing=True,
    )


def _get_permissions_table() -> sa.Table:
    """Local definition matching the current (post-f41bbe0c0f12) schema where
    ``permission_group_id`` has been replaced by direct ``role_id`` / scope
    columns on the ``permissions`` table."""
    return sa.Table(
        "permissions",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("role_id", GUID, nullable=False),
        sa.Column("scope_type", sa.VARCHAR(length=32), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False),
        extend_existing=True,
    )


def _member_role_name(project_id: uuid.UUID) -> str:
    """Match ProjectMemberRoleSpec.role_name() used by the runtime create path."""
    return f"project-{str(project_id)[:8]}-member"


def _legacy_member_role_name(project_id: uuid.UUID) -> str:
    """Name used by the original migration 430b1631804d for member roles."""
    return f"role_project_{str(project_id)[:8]}_member"


def _query_projects_missing_member_role(db_conn: Connection) -> Sequence[Row[Any]]:
    """Return groups.id for every project that has no member role bound at
    its project scope, regardless of the role's source or naming convention.

    A project is considered to already have a member role if there exists any
    role bound in association_scopes_entities at (PROJECT, project_id) whose
    name matches either the runtime naming convention or the legacy naming
    convention for that project id.
    """
    groups_table = _get_groups_table()
    roles_table = get_roles_table()
    assoc_table = get_association_scopes_entities_table()

    runtime_pattern = (
        "project-" + sa.func.substring(sa.cast(groups_table.c.id, sa.String), 1, 8) + "-member"
    )
    legacy_pattern = (
        "role_project_" + sa.func.substring(sa.cast(groups_table.c.id, sa.String), 1, 8) + "_member"
    )

    member_exists_subq = (
        sa.select(sa.literal(1))
        .select_from(
            assoc_table.join(
                roles_table,
                sa.cast(assoc_table.c.entity_id, sa.String) == sa.cast(roles_table.c.id, sa.String),
            )
        )
        .where(
            assoc_table.c.scope_type == ScopeType.PROJECT,
            assoc_table.c.scope_id == sa.cast(groups_table.c.id, sa.String),
            assoc_table.c.entity_type == "role",
            sa.or_(
                roles_table.c.name == runtime_pattern,
                roles_table.c.name == legacy_pattern,
            ),
        )
    ).exists()

    query = sa.select(groups_table.c.id).where(sa.not_(member_exists_subq))
    return list(db_conn.execute(query).all())


def _create_member_roles_for_projects(
    db_conn: Connection, project_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, uuid.UUID]:
    """Create a SYSTEM-sourced member role row per project.

    Returns a mapping {project_id -> role_id}. Uses insert_skip_on_conflict so
    that a partially-applied previous run cannot produce duplicate rows, and
    then re-queries by name to resolve the role ids.
    """
    if not project_ids:
        return {}

    roles_table = get_roles_table()
    role_inputs: list[dict[str, Any]] = []
    name_to_project: dict[str, uuid.UUID] = {}
    for project_id in project_ids:
        name = _member_role_name(project_id)
        role_inputs.append({
            "name": name,
            "source": RoleSource.SYSTEM,
            "status": RoleStatus.ACTIVE,
        })
        name_to_project[name] = project_id

    # The roles table has no unique constraint on name, so insert_skip_on_conflict
    # would not help here. The outer filter query is what keeps us idempotent.
    db_conn.execute(sa.insert(roles_table), role_inputs)

    role_rows = query_role_rows_by_name(db_conn, list(name_to_project.keys()))
    project_to_role: dict[uuid.UUID, uuid.UUID] = {}
    for row in role_rows:
        resolved = name_to_project.get(row.name)
        if resolved is None:
            continue
        project_to_role[resolved] = row.id
    return project_to_role


def _bind_roles_to_project_scopes(
    db_conn: Connection, project_to_role: dict[uuid.UUID, uuid.UUID]
) -> None:
    if not project_to_role:
        return
    assoc_table = get_association_scopes_entities_table()
    rows = [
        {
            "scope_type": ScopeType.PROJECT,
            "scope_id": str(project_id),
            "entity_type": "role",
            "entity_id": str(role_id),
        }
        for project_id, role_id in project_to_role.items()
    ]
    insert_skip_on_conflict(db_conn, assoc_table, rows)


def _create_member_permissions(
    db_conn: Connection, project_to_role: dict[uuid.UUID, uuid.UUID]
) -> None:
    if not project_to_role:
        return
    permissions_table = _get_permissions_table()
    rows: list[dict[str, Any]] = []
    for project_id, role_id in project_to_role.items():
        for entity_type in _MEMBER_ACCESSIBLE_ENTITY_TYPES:
            for operation in _MEMBER_OPERATIONS:
                rows.append({
                    "role_id": role_id,
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": str(project_id),
                    "entity_type": entity_type,
                    "operation": operation,
                })
    insert_skip_on_conflict(db_conn, permissions_table, rows)


def _promote_legacy_member_roles_to_system(db_conn: Connection) -> None:
    """Promote legacy project member roles (``role_project_{id8}_member``) that
    were created with ``source = custom`` by migration ``430b1631804d`` so that
    every project member role has ``source = system``.

    Only roles whose (a) name matches the legacy member role pattern and
    (b) are bound in ``association_scopes_entities`` at PROJECT scope are
    updated, to avoid touching any unrelated custom role. The filter is
    idempotent: roles that are already ``system`` simply match zero rows.
    """
    roles_table = get_roles_table()
    assoc_table = get_association_scopes_entities_table()

    legacy_scope_subq = (
        sa.select(sa.literal(1))
        .select_from(assoc_table)
        .where(
            assoc_table.c.scope_type == ScopeType.PROJECT,
            assoc_table.c.entity_type == "role",
            sa.cast(assoc_table.c.entity_id, sa.String) == sa.cast(roles_table.c.id, sa.String),
        )
        .exists()
    )

    stmt = (
        sa.update(roles_table)
        .where(
            roles_table.c.name.like("role_project_%_member"),
            roles_table.c.source == RoleSource.CUSTOM,
            legacy_scope_subq,
        )
        .values(source=RoleSource.SYSTEM)
    )
    db_conn.execute(stmt)


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Backfill member roles for projects that have none.
    project_rows = _query_projects_missing_member_role(conn)
    project_ids: list[uuid.UUID] = [row.id for row in project_rows]
    if project_ids:
        project_to_role = _create_member_roles_for_projects(conn, project_ids)
        _bind_roles_to_project_scopes(conn, project_to_role)
        _create_member_permissions(conn, project_to_role)

    # 2. Promote legacy CUSTOM member roles to SYSTEM so that all project
    #    member roles have a consistent source across the database.
    _promote_legacy_member_roles_to_system(conn)


def downgrade() -> None:
    # We cannot safely distinguish backfilled member roles from those that
    # existed beforehand, and the pre-upgrade source of legacy roles is not
    # recorded anywhere, so downgrade is intentionally a no-op.
    pass
