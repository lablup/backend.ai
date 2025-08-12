"""migrate user data to roles

Revision ID: a4d56e86d9ee
Revises: 34362a3b065d
Create Date: 2025-08-06 21:28:29.354670

"""

import enum
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.models.base import EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
    get_permission_groups_table,
    get_permissions_table,
    get_roles_table,
    get_user_roles_table,
    mapper_registry,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    PermissionCreateInput,
    ScopePermissionGroupCreateInput,
    UserRoleCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    UserData,
    get_user_self_role_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_if_data_exists,
)

# revision identifiers, used by Alembic.
revision = "a4d56e86d9ee"
down_revision = "34362a3b065d"
branch_labels = None
depends_on = None


OWNER_ACCESSIBLE_ENTITY_TYPES_IN_USER: set[EntityType] = set()


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


def _get_users_table() -> sa.Table:
    users_table = sa.Table(
        "users",
        mapper_registry.metadata,
        IDColumn("uuid"),
        sa.Column("username", sa.String(length=64), unique=True),
        sa.Column("domain_name", sa.String(length=64), index=True),
        sa.Column("role", EnumValueType(UserRole), default=UserRole.USER),
        extend_existing=True,
    )
    return users_table


def _query_user_row(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query all user rows with pagination.
    """
    users_table = _get_users_table()
    user_query = (
        sa.select(
            users_table.c.uuid,
            users_table.c.username,
            users_table.c.domain_name,
            users_table.c.role,
        )
        .offset(offset)
        .limit(page_size)
        .order_by(users_table.c.uuid)
    )
    return db_conn.execute(user_query).all()


def _query_role_rows_by_name(db_conn: Connection, role_names: Iterable[str]) -> list[Row]:
    """
    Query role rows by their names.
    """
    roles_table = get_roles_table()
    role_query = sa.select(roles_table).where(roles_table.c.name.in_(role_names))
    return db_conn.execute(role_query).all()


def _create_roles_from_user_rows(db_conn: Connection, rows: Sequence[Row]) -> dict[str, uuid.UUID]:
    roles_table = get_roles_table()
    role_inputs: list[dict[str, Any]] = []
    role_name_user_id_map: dict[str, uuid.UUID] = {}
    for row in rows:
        data = UserData.from_row(row)
        role_input = get_user_self_role_creation_input(data)
        role_inputs.append(role_input.to_dict())
        role_name_user_id_map[role_input.name] = data.id
    insert_if_data_exists(db_conn, roles_table, role_inputs)
    return role_name_user_id_map


def _create_permission_groups_for_user_role(
    db_conn: Connection, role_id_user_id_map: Mapping[uuid.UUID, uuid.UUID]
) -> None:
    permission_groups_table = get_permission_groups_table()
    permission_group_inputs: list[dict[str, Any]] = []
    for role_id, user_id in role_id_user_id_map.items():
        input = ScopePermissionGroupCreateInput(
            role_id=role_id,
            scope_type=ScopeType.USER,
            scope_id=str(user_id),
        )
        permission_group_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, permission_groups_table, permission_group_inputs)


def _query_permission_groups_by_scope_ids(
    db_conn: Connection, scope_ids: Iterable[str]
) -> list[uuid.UUID]:
    """
    Query permission groups by scope IDs.
    """
    permission_groups_table = get_permission_groups_table()
    query = sa.select(permission_groups_table.c.id).where(
        permission_groups_table.c.scope_id.in_(scope_ids)
    )
    return db_conn.scalars(query).all()


def _create_user_roles_from_mapping(
    db_conn: Connection, role_id_user_id_map: Mapping[uuid.UUID, uuid.UUID]
) -> None:
    user_roles_table = get_user_roles_table()
    user_role_inputs: list[UserRoleCreateInput] = []
    for role_id, user_id in role_id_user_id_map.items():
        user_role_input = UserRoleCreateInput(user_id=user_id, role_id=role_id)
        user_role_inputs.append(user_role_input)
    insert_if_data_exists(
        db_conn, user_roles_table, [input.to_dict() for input in user_role_inputs]
    )


def _create_permissions_for_user_self_roles(
    db_conn: Connection,
    permission_group_ids: Iterable[uuid.UUID],
) -> None:
    scope_permission_inputs: list[dict[str, Any]] = []
    for permission_group_id in permission_group_ids:
        for entity_type in OWNER_ACCESSIBLE_ENTITY_TYPES_IN_USER:
            for operation in OperationType.owner_operations():
                input = PermissionCreateInput(
                    permission_group_id=permission_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                scope_permission_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, get_permissions_table(), scope_permission_inputs)


def _create_user_self_roles_and_permissions(db_conn: Connection) -> None:
    """
    Migrate user data to roles and permissions.
    All users have a default self role and permissions.
    """
    offset = 0
    page_size = 1000
    while True:
        rows = _query_user_row(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        role_name_user_id_map = _create_roles_from_user_rows(db_conn, rows)
        role_rows = _query_role_rows_by_name(db_conn, list(role_name_user_id_map.keys()))
        role_id_user_id_map: dict[uuid.UUID, uuid.UUID] = {
            row.id: role_name_user_id_map[row.name] for row in role_rows
        }
        _create_user_roles_from_mapping(db_conn, role_id_user_id_map)
        _create_permission_groups_for_user_role(db_conn, role_id_user_id_map)
        str_user_ids = [str(user_id) for user_id in role_id_user_id_map.values()]
        permission_group_ids = _query_permission_groups_by_scope_ids(db_conn, str_user_ids)
        _create_permissions_for_user_self_roles(db_conn, permission_group_ids)


def upgrade() -> None:
    conn = op.get_bind()
    _create_user_self_roles_and_permissions(conn)


def downgrade() -> None:
    conn = op.get_bind()
    # Remove all data from the new RBAC tables
    conn.execute(sa.delete(get_association_scopes_entities_table()))
    conn.execute(sa.delete(get_permissions_table()))
    conn.execute(sa.delete(get_permission_groups_table()))
    conn.execute(sa.delete(get_user_roles_table()))
    conn.execute(sa.delete(get_roles_table()))
