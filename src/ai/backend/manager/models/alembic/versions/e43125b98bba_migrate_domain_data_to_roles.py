"""migrate domain data to roles

Revision ID: e43125b98bba
Revises: 430b1631804d
Create Date: 2025-08-12 15:38:26.989485

"""

import enum
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.base import EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
    RoleSource,
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
    AssociationScopesEntitiesCreateInput,
    PermissionCreateInput,
    ScopePermissionGroupCreateInput,
    UserRoleCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    DomainData,
    get_domain_admin_role_creation_input,
    get_domain_member_role_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_if_data_exists,
    query_permission_groups_by_scope_ids,
    query_role_rows_by_name,
)

# revision identifiers, used by Alembic.
revision = "e43125b98bba"
down_revision = "430b1631804d"
branch_labels = None
depends_on = None

ADMIN_ACCESSIBLE_ENTITY_TYPES_IN_DOMAIN: set[EntityType] = {
    EntityType.USER,
}
MEMBER_ACCESSIBLE_ENTITY_TYPES_IN_DOMAIN: set[EntityType] = set()


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


def _get_domains_table() -> sa.Table:
    domains_table = sa.Table(
        "domains",
        mapper_registry.metadata,
        sa.Column("name", sa.Unicode(length=64), primary_key=True),
        extend_existing=True,
    )
    return domains_table


def _query_domain_row(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query all domain rows with pagination.
    """
    domains_table = _get_domains_table()
    domain_query = (
        sa.select(domains_table.c.name)
        .offset(offset)
        .limit(page_size)
        .order_by(domains_table.c.name)
    )
    return db_conn.execute(domain_query).all()


def _create_admin_roles_from_domain_rows(
    db_conn: Connection, rows: Sequence[Row]
) -> dict[str, str]:
    roles_table = get_roles_table()
    role_inputs: list[dict[str, Any]] = []
    role_name_domain_name_map: dict[str, str] = {}
    for row in rows:
        data = DomainData.from_row(row)
        role_input = get_domain_admin_role_creation_input(data)
        role_inputs.append(role_input.to_dict())
        role_name_domain_name_map[role_input.name] = data.name
    insert_if_data_exists(db_conn, roles_table, role_inputs)
    return role_name_domain_name_map


def _create_member_roles_from_domain_rows(
    db_conn: Connection, rows: Sequence[Row]
) -> dict[str, str]:
    roles_table = get_roles_table()
    role_inputs: list[dict[str, Any]] = []
    role_name_domain_name_map: dict[str, str] = {}
    for row in rows:
        data = DomainData.from_row(row)
        role_input = get_domain_member_role_creation_input(data)
        role_inputs.append(role_input.to_dict())
        role_name_domain_name_map[role_input.name] = data.name
    insert_if_data_exists(db_conn, roles_table, role_inputs)
    return role_name_domain_name_map


def _create_permission_groups_for_domain_role(
    db_conn: Connection, role_id_domain_name_map: Mapping[uuid.UUID, str]
) -> None:
    permission_groups_table = get_permission_groups_table()
    permission_group_inputs: list[dict[str, Any]] = []
    for role_id, domain_name in role_id_domain_name_map.items():
        input = ScopePermissionGroupCreateInput(
            role_id=role_id,
            scope_type=ScopeType.DOMAIN,
            scope_id=domain_name,
        )
        permission_group_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, permission_groups_table, permission_group_inputs)


def _create_permissions_for_domain_admin_roles(
    db_conn: Connection,
    permission_group_ids: Iterable[uuid.UUID],
) -> None:
    scope_permission_inputs: list[dict[str, Any]] = []
    for permission_group_id in permission_group_ids:
        for entity_type in ADMIN_ACCESSIBLE_ENTITY_TYPES_IN_DOMAIN:
            for operation in OperationType.admin_operations():
                input = PermissionCreateInput(
                    permission_group_id=permission_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                scope_permission_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, get_permissions_table(), scope_permission_inputs)


def _create_permissions_for_domain_member_roles(
    db_conn: Connection,
    permission_group_ids: Iterable[uuid.UUID],
) -> None:
    scope_permission_inputs: list[dict[str, Any]] = []
    for permission_group_id in permission_group_ids:
        for entity_type in MEMBER_ACCESSIBLE_ENTITY_TYPES_IN_DOMAIN:
            for operation in OperationType.member_operations():
                input = PermissionCreateInput(
                    permission_group_id=permission_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                scope_permission_inputs.append(input.to_dict())
    insert_if_data_exists(db_conn, get_permissions_table(), scope_permission_inputs)


def _create_domain_admin_roles_and_permissions(db_conn: Connection, rows: Sequence[Row]) -> None:
    role_name_domain_name_map = _create_admin_roles_from_domain_rows(db_conn, rows)
    role_rows = query_role_rows_by_name(db_conn, list(role_name_domain_name_map.keys()))
    role_id_domain_name_map: dict[uuid.UUID, str] = {
        row.id: role_name_domain_name_map[row.name] for row in role_rows
    }
    _create_permission_groups_for_domain_role(db_conn, role_id_domain_name_map)
    permission_group_ids = query_permission_groups_by_scope_ids(
        db_conn, list(role_id_domain_name_map.values())
    )
    _create_permissions_for_domain_admin_roles(db_conn, permission_group_ids)


def _create_domain_member_roles_and_permissions(db_conn: Connection, rows: Sequence[Row]) -> None:
    role_name_domain_name_map = _create_member_roles_from_domain_rows(db_conn, rows)
    role_rows = query_role_rows_by_name(db_conn, list(role_name_domain_name_map.keys()))
    role_id_domain_name_map: dict[uuid.UUID, str] = {
        row.id: role_name_domain_name_map[row.name] for row in role_rows
    }
    _create_permission_groups_for_domain_role(db_conn, role_id_domain_name_map)
    permission_group_ids = query_permission_groups_by_scope_ids(
        db_conn, list(role_id_domain_name_map.values())
    )
    _create_permissions_for_domain_member_roles(db_conn, permission_group_ids)


def _create_domain_roles_and_permissions(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        rows = _query_domain_row(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        _create_domain_admin_roles_and_permissions(db_conn, rows)
        _create_domain_member_roles_and_permissions(db_conn, rows)


def _query_user_domain_role_mapping_rows(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    roles_table = get_roles_table()
    users_table = _get_users_table()
    permission_groups_table = get_permission_groups_table()

    stmt = (
        sa.select(
            users_table.c.uuid.label("user_id"),
            users_table.c.role,
            users_table.c.domain_name,
            roles_table.c.source,
            permission_groups_table.c.role_id,
        )
        .select_from(
            sa.join(
                users_table,
                permission_groups_table,
                users_table.c.domain_name == permission_groups_table.c.scope_id,
            ).join(
                roles_table,
                permission_groups_table.c.role_id == roles_table.c.id,
            )
        )
        .offset(offset)
        .limit(page_size)
        .order_by(users_table.c.uuid)
    )
    return db_conn.execute(stmt).all()


def _map_users_to_domain_role(db_conn: Connection) -> None:
    user_roles_table = get_user_roles_table()
    association_scopes_entities_table = get_association_scopes_entities_table()

    offset = 0
    page_size = 1000

    while True:
        rows = _query_user_domain_role_mapping_rows(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        user_role_mapping_inputs: list[dict[str, Any]] = []
        association_inputs: list[dict[str, Any]] = []
        for row in rows:
            user_role = cast(UserRole, row.role)
            match user_role:
                case UserRole.SUPERADMIN:
                    continue
                case UserRole.ADMIN:
                    if row.source == RoleSource.SYSTEM:
                        user_role_mapping_inputs.append(
                            UserRoleCreateInput(user_id=row.user_id, role_id=row.role_id).to_dict()
                        )
                        input = AssociationScopesEntitiesCreateInput(
                            scope_id=ScopeId(
                                scope_type=ScopeType.DOMAIN.to_original(),
                                scope_id=row.domain_name,
                            ),
                            object_id=ObjectId(
                                entity_type=EntityType.USER.to_original(),
                                entity_id=str(row.user_id),
                            ),
                        )
                        association_inputs.append(input.to_dict())
                case UserRole.USER:
                    if row.source == RoleSource.CUSTOM:
                        user_role_mapping_inputs.append(
                            UserRoleCreateInput(user_id=row.user_id, role_id=row.role_id).to_dict()
                        )
                        input = AssociationScopesEntitiesCreateInput(
                            scope_id=ScopeId(
                                scope_type=ScopeType.DOMAIN.to_original(),
                                scope_id=row.domain_name,
                            ),
                            object_id=ObjectId(
                                entity_type=EntityType.USER.to_original(),
                                entity_id=str(row.user_id),
                            ),
                        )
                        association_inputs.append(input.to_dict())
                case UserRole.MONITOR:
                    pass
        insert_if_data_exists(db_conn, user_roles_table, user_role_mapping_inputs)
        insert_if_data_exists(
            db_conn,
            association_scopes_entities_table,
            association_inputs,
        )


def _map_projects_to_domain_scope(db_conn: Connection) -> None:
    projects_table = _get_groups_table()
    association_scopes_entities_table = get_association_scopes_entities_table()

    offset = 0
    page_size = 1000

    while True:
        stmt = (
            sa.select(projects_table.c.id, projects_table.c.domain_name)
            .select_from(projects_table)
            .offset(offset)
            .limit(page_size)
            .order_by(projects_table.c.id)
        )
        rows = db_conn.execute(stmt).all()
        offset += page_size
        if not rows:
            break
        input_data = [
            {
                "scope_type": ScopeType.DOMAIN,
                "scope_id": row.domain_name,
                "entity_type": EntityType.PROJECT,
                "entity_id": str(row.id),
            }
            for row in rows
        ]
        insert_if_data_exists(db_conn, association_scopes_entities_table, input_data)


def upgrade() -> None:
    conn = op.get_bind()
    _create_domain_roles_and_permissions(conn)
    _map_users_to_domain_role(conn)
    _map_projects_to_domain_scope(conn)


def downgrade() -> None:
    pass
