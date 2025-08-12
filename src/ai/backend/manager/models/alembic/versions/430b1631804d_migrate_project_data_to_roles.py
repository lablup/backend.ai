"""migrate project data to roles

Revision ID: 430b1631804d
Revises: a4d56e86d9ee
Create Date: 2025-08-12 15:30:10.369554

"""

import enum
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_permission_groups_table,
    get_permissions_table,
    get_roles_table,
    mapper_registry,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    PermissionCreateInput,
    ScopePermissionGroupCreateInput,
    UserRoleMappingCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    ProjectData,
    UserScopeRoleMappingArgs,
    get_project_admin_role_creation_input,
    get_project_member_role_creation_input,
    get_user_project_mapping_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_from_user_role_mapping_input_group,
    insert_if_data_exists,
    query_permission_groups_by_scope_ids,
    query_role_rows_by_name,
)

# revision identifiers, used by Alembic.
revision = "430b1631804d"
down_revision = "a4d56e86d9ee"
branch_labels = None
depends_on = None

ADMIN_ACCESSIBLE_ENTITY_TYPES_IN_PROJECT = {
    EntityType.USER,
}
MEMBER_ACCESSIBLE_ENTITY_TYPES_IN_PROJECT = {
    EntityType.USER,
}


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


def _get_groups_table() -> sa.Table:
    groups_table = sa.Table(
        "groups",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        extend_existing=True,
    )
    return groups_table


def _get_association_groups_users_table() -> sa.Table:
    association_groups_users_table = sa.Table(
        "association_groups_users",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("user_id", GUID, nullable=False),
        sa.Column(
            "group_id",
            GUID,
            sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        extend_existing=True,
    )
    return association_groups_users_table


def _query_project_row(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query all project rows with pagination.
    """
    groups_table = _get_groups_table()
    project_query = (
        sa.select(groups_table.c.id).offset(offset).limit(page_size).order_by(groups_table.c.id)
    )
    return db_conn.execute(project_query).all()


def _create_admin_roles_from_project_rows(
    db_conn: Connection, rows: Sequence[Row]
) -> dict[str, uuid.UUID]:
    roles_table = get_roles_table()
    role_inputs: list[dict[str, Any]] = []
    role_name_project_id_map: dict[str, uuid.UUID] = {}
    for row in rows:
        data = ProjectData.from_row(row)
        admin_role_input = get_project_admin_role_creation_input(data)
        role_inputs.append(admin_role_input.to_dict())
        role_name_project_id_map[admin_role_input.name] = data.id

    insert_if_data_exists(db_conn, roles_table, role_inputs)
    return role_name_project_id_map


def _create_member_roles_from_project_rows(
    db_conn: Connection, rows: Sequence[Row]
) -> dict[str, uuid.UUID]:
    roles_table = get_roles_table()
    role_inputs: list[dict[str, Any]] = []
    role_name_project_id_map: dict[str, uuid.UUID] = {}
    for row in rows:
        data = ProjectData.from_row(row)
        member_role_input = get_project_member_role_creation_input(data)
        role_inputs.append(member_role_input.to_dict())
        role_name_project_id_map[member_role_input.name] = data.id

    insert_if_data_exists(db_conn, roles_table, role_inputs)
    return role_name_project_id_map


def _create_permission_groups_for_project_role(
    db_conn: Connection, role_id_project_id_map: Mapping[uuid.UUID, uuid.UUID]
) -> None:
    permission_groups_table = get_permission_groups_table()
    permission_group_inputs: list[dict[str, Any]] = []
    for role_id, project_id in role_id_project_id_map.items():
        input = ScopePermissionGroupCreateInput(
            role_id=role_id,
            scope_type=ScopeType.PROJECT,
            scope_id=str(project_id),
        )
        permission_group_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, permission_groups_table, permission_group_inputs)


def _create_admin_permissions_for_project_roles(
    db_conn: Connection, permission_group_ids: Iterable[uuid.UUID]
) -> None:
    scope_permission_inputs: list[dict[str, Any]] = []
    for permission_group_id in permission_group_ids:
        for entity_type in ADMIN_ACCESSIBLE_ENTITY_TYPES_IN_PROJECT:
            for operation in OperationType.admin_operations():
                input = PermissionCreateInput(
                    permission_group_id=permission_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                scope_permission_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, get_permissions_table(), scope_permission_inputs)


def _create_member_permissions_for_project_roles(
    db_conn: Connection, permission_group_ids: Iterable[uuid.UUID]
) -> None:
    scope_permission_inputs: list[dict[str, Any]] = []
    for permission_group_id in permission_group_ids:
        for entity_type in MEMBER_ACCESSIBLE_ENTITY_TYPES_IN_PROJECT:
            for operation in OperationType.member_operations():
                input = PermissionCreateInput(
                    permission_group_id=permission_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                scope_permission_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, get_permissions_table(), scope_permission_inputs)


def _create_project_admin_roles_and_permissions(db_conn: Connection, rows: Sequence[Row]) -> None:
    admin_role_name_project_id_map = _create_admin_roles_from_project_rows(db_conn, rows)
    role_rows = query_role_rows_by_name(db_conn, list(admin_role_name_project_id_map.keys()))
    role_id_project_id_map: dict[uuid.UUID, uuid.UUID] = {
        row.id: admin_role_name_project_id_map[row.name] for row in role_rows
    }
    _create_permission_groups_for_project_role(db_conn, role_id_project_id_map)
    str_project_ids = [str(user_id) for user_id in role_id_project_id_map.values()]
    permission_group_ids = query_permission_groups_by_scope_ids(db_conn, str_project_ids)
    _create_admin_permissions_for_project_roles(db_conn, permission_group_ids)


def _create_project_member_roles_and_permissions(db_conn: Connection, rows: Sequence[Row]) -> None:
    member_role_name_project_id_map = _create_member_roles_from_project_rows(db_conn, rows)
    role_rows = query_role_rows_by_name(db_conn, list(member_role_name_project_id_map.keys()))
    role_id_project_id_map: dict[uuid.UUID, uuid.UUID] = {
        row.id: member_role_name_project_id_map[row.name] for row in role_rows
    }
    _create_permission_groups_for_project_role(db_conn, role_id_project_id_map)
    str_project_ids = [str(user_id) for user_id in role_id_project_id_map.values()]
    permission_group_ids = query_permission_groups_by_scope_ids(db_conn, str_project_ids)
    _create_member_permissions_for_project_roles(db_conn, permission_group_ids)


def _create_project_roles_and_permissions(db_conn: Connection) -> None:
    """
    Migrate project data to roles and permissions.
    All projects have a default admin role and a member role.
    """
    offset = 0
    page_size = 1000
    while True:
        rows = _query_project_row(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        _create_project_admin_roles_and_permissions(db_conn, rows)
        _create_project_member_roles_and_permissions(db_conn, rows)


def _query_admin_project_role_mapping_rows(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    users_table = _get_users_table()
    roles_table = get_roles_table()
    groups_table = _get_groups_table()
    permission_groups_table = get_permission_groups_table()
    stmt = (
        sa.select(
            users_table.c.uuid.label("user_id"),
            users_table.c.domain_name,
            users_table.c.role.label("user_role"),
            groups_table.c.id.label("project_id"),
            roles_table.c.source.label("role_source"),
        )
        .select_from(
            sa.join(
                users_table,
                groups_table,
                users_table.c.domain_name == groups_table.c.domain_name,
            )
            .join(
                permission_groups_table,
                groups_table.c.id == sa.cast(permission_groups_table.c.scope_id, PGUUID),
            )
            .join(
                roles_table,
                roles_table.c.id == permission_groups_table.c.role_id,
            )
        )
        .where(
            sa.and_(
                roles_table.c.source == RoleSource.SYSTEM,
                users_table.c.role == UserRole.ADMIN,
            )
        )
        .offset(offset)
        .limit(page_size)
        .order_by(users_table.c.uuid)
    )
    return db_conn.execute(stmt).all()


def _map_admin_users_to_project_role(db_conn: Connection) -> None:
    """
    Map domain admin users to project admin roles.
    """
    offset = 0
    page_size = 1000

    while True:
        rows = _query_admin_project_role_mapping_rows(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_groups: list[UserRoleMappingCreateInput] = []
        for row in rows:
            args = UserScopeRoleMappingArgs(
                user_id=row.user_id,
                user_role=row.user_role,
                scope_id=ScopeId(
                    scope_type=ScopeType.PROJECT.to_original(),
                    scope_id=str(row.project_id),
                ),
                role_id=row.role_id,
                role_source=row.role_source,
            )
            input_data = get_user_project_mapping_creation_input(args)
            if input_data is not None:
                input_groups.append(input_data)
        insert_from_user_role_mapping_input_group(db_conn, input_groups)


def _query_user_project_role_mapping_rows(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    users_table = _get_users_table()
    roles_table = get_roles_table()
    permission_groups_table = get_permission_groups_table()
    association_groups_users = _get_association_groups_users_table()
    stmt = (
        sa.select(
            users_table.c.uuid.label("user_id"),
            users_table.c.role.label("user_role"),
            association_groups_users.c.group_id.label("project_id"),
            permission_groups_table.c.role_id,
            roles_table.c.source.label("role_source"),
        )
        .select_from(
            sa.join(
                users_table,
                association_groups_users,
                users_table.c.uuid == association_groups_users.c.user_id,
            )
            .join(
                permission_groups_table,
                association_groups_users.c.group_id
                == sa.cast(permission_groups_table.c.scope_id, PGUUID),
            )
            .join(
                roles_table,
                roles_table.c.id == permission_groups_table.c.role_id,
            )
        )
        .where(roles_table.c.source == RoleSource.CUSTOM)
        .offset(offset)
        .limit(page_size)
        .order_by(users_table.c.uuid)
    )
    return db_conn.execute(stmt).all()


def _map_member_users_to_project_role(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000

    while True:
        rows = _query_user_project_role_mapping_rows(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_groups: list[UserRoleMappingCreateInput] = []
        for row in rows:
            args = UserScopeRoleMappingArgs(
                user_id=row.user_id,
                user_role=row.user_role,
                scope_id=ScopeId(
                    scope_type=ScopeType.PROJECT.to_original(),
                    scope_id=str(row.project_id),
                ),
                role_id=row.role_id,
                role_source=row.role_source,
            )
            input_data = get_user_project_mapping_creation_input(args)
            if input_data is not None:
                input_groups.append(input_data)
        insert_from_user_role_mapping_input_group(db_conn, input_groups)


def _map_users_to_project_role(db_conn: Connection) -> None:
    """
    Map users to project roles.
    """
    _map_admin_users_to_project_role(db_conn)
    _map_member_users_to_project_role(db_conn)


def upgrade() -> None:
    conn = op.get_bind()
    _create_project_roles_and_permissions(conn)
    _map_users_to_project_role(conn)


def downgrade() -> None:
    pass
