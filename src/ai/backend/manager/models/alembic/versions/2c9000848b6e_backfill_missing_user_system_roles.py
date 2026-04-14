"""backfill missing user system roles

Users created via the signup or OpenID flows after migration a4d56e86d9ee
were not assigned RBAC system roles. This idempotent migration creates
system roles, permissions, and user_roles mappings
for any user that lacks a user_roles entry.

Revision ID: 2c9000848b6e
Revises: 4f08ccd6cb8e
Create Date: 2026-04-08 12:00:00.000000

"""

import uuid
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.enums import (
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_roles_table,
    get_user_roles_table,
    mapper_registry,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    UserRoleCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    ENTITY_TYPES_IN_ROLE,
    OPERATIONS_IN_ROLE,
    UserRole,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_skip_on_conflict,
    query_role_rows_by_name,
)

# revision identifiers, used by Alembic.
revision = "2c9000848b6e"
down_revision = "4f08ccd6cb8e"
branch_labels = None
depends_on = None


def _get_permissions_table() -> sa.Table:
    """Local definition matching the current schema (post-f41bbe0c0f12)
    where permission_group_id has been replaced by direct role_id/scope columns."""
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


def _get_users_table() -> sa.Table:
    return sa.Table(
        "users",
        mapper_registry.metadata,
        IDColumn("uuid"),
        sa.Column("username", sa.String(length=64), unique=True),
        sa.Column("domain_name", sa.String(length=64), index=True),
        sa.Column("role", EnumValueType(UserRole), default=UserRole.USER),
        extend_existing=True,
    )


def _role_name(user_uuid: uuid.UUID) -> str:
    """Match the naming convention used by the current code path
    (UserData.role_name in manager/data/user/types.py)."""
    return f"user-{str(user_uuid)[:8]}"


def _query_users_without_system_roles(
    db_conn: Connection, offset: int, page_size: int
) -> Sequence[Row[Any]]:
    users_table = _get_users_table()
    user_roles_table = get_user_roles_table()
    roles_table = get_roles_table()
    # Subquery: user_ids that already have a system role
    system_role_subq = (
        sa.select(user_roles_table.c.user_id)
        .join(roles_table, user_roles_table.c.role_id == roles_table.c.id)
        .where(roles_table.c.source == RoleSource.SYSTEM)
    ).subquery()
    query = (
        sa.select(
            users_table.c.uuid,
            users_table.c.username,
            users_table.c.domain_name,
            users_table.c.role,
        )
        .where(users_table.c.uuid.notin_(sa.select(system_role_subq.c.user_id)))
        .offset(offset)
        .limit(page_size)
        .order_by(users_table.c.uuid)
    )
    return db_conn.execute(query).all()


def _backfill_roles_and_permissions(db_conn: Connection, rows: Sequence[Row[Any]]) -> None:
    roles_table = get_roles_table()
    from ai.backend.manager.models.rbac_models.migration.enums import RoleSource, RoleStatus

    # Create roles (skip if already exists by name)
    role_inputs: list[dict[str, Any]] = []
    uuid_by_role_name: dict[str, uuid.UUID] = {}
    for row in rows:
        name = _role_name(row.uuid)
        role_inputs.append({"name": name, "source": RoleSource.SYSTEM, "status": RoleStatus.ACTIVE})
        uuid_by_role_name[name] = row.uuid
    insert_skip_on_conflict(db_conn, roles_table, role_inputs)

    # Resolve role IDs
    role_rows = query_role_rows_by_name(db_conn, list(uuid_by_role_name.keys()))
    role_id_user_id_map: dict[uuid.UUID, uuid.UUID] = {
        r.id: uuid_by_role_name[r.name] for r in role_rows
    }

    # Create permissions directly (post-f41bbe0c0f12 denormalized schema)
    permissions_table = _get_permissions_table()
    perm_inputs: list[dict[str, Any]] = []
    for role_id, user_id in role_id_user_id_map.items():
        for entity_type in ENTITY_TYPES_IN_ROLE:
            for operation in OPERATIONS_IN_ROLE:
                perm_inputs.append({
                    "role_id": role_id,
                    "scope_type": ScopeType.USER,
                    "scope_id": str(user_id),
                    "entity_type": entity_type,
                    "operation": operation,
                })
    insert_skip_on_conflict(db_conn, permissions_table, perm_inputs)

    # Create user-role mappings
    ur_inputs: list[dict[str, Any]] = []
    for role_id, user_id in role_id_user_id_map.items():
        ur_inputs.append(UserRoleCreateInput(user_id=user_id, role_id=role_id).to_dict())
    insert_skip_on_conflict(db_conn, get_user_roles_table(), ur_inputs)


def upgrade() -> None:
    conn = op.get_bind()
    offset = 0
    page_size = 1000
    while True:
        rows = _query_users_without_system_roles(conn, offset, page_size)
        if not rows:
            break
        _backfill_roles_and_permissions(conn, rows)
        # Don't increment offset — the query filters out users that already
        # have roles, so processed users will no longer appear in results.


def downgrade() -> None:
    pass
