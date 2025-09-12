"""migrate user data to roles

Revision ID: a4d56e86d9ee
Revises: 9adcd6f48ba1
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
    ScopeType,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_permission_groups_table,
    get_permissions_table,
    get_roles_table,
    get_user_roles_table,
    mapper_registry,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    PermissionCreateInput,
    PermissionGroupCreateInput,
    UserRoleCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    ENTITY_TYPES_IN_ROLE,
    OPERATIONS_IN_ROLE,
    UserData,
    get_user_self_role_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_if_data_exists,
    query_permission_groups_by_scope_ids,
    query_role_rows_by_name,
)

# revision identifiers, used by Alembic.
revision = "a4d56e86d9ee"
down_revision = "9adcd6f48ba1"
branch_labels = None
depends_on = None


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


class Tables:
    @staticmethod
    def get_users_table() -> sa.Table:
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


class RoleCreator:
    @classmethod
    def _create_self_roles(cls, db_conn: Connection, rows: Sequence[Row]) -> dict[str, uuid.UUID]:
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

    @classmethod
    def _create_permission_groups(
        cls, db_conn: Connection, role_id_user_id_map: Mapping[uuid.UUID, uuid.UUID]
    ) -> None:
        permission_groups_table = get_permission_groups_table()
        permission_group_inputs: list[dict[str, Any]] = []
        for role_id, user_id in role_id_user_id_map.items():
            input = PermissionGroupCreateInput(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id=str(user_id),
            )
            permission_group_inputs.append(input.to_dict())
        insert_if_data_exists(db_conn, permission_groups_table, permission_group_inputs)

    @classmethod
    def _create_permissions(
        cls, db_conn: Connection, permission_group_ids: Iterable[uuid.UUID]
    ) -> None:
        permission_inputs: list[dict[str, Any]] = []
        for permission_group_id in permission_group_ids:
            for entity_type in ENTITY_TYPES_IN_ROLE:
                for operation in OPERATIONS_IN_ROLE:
                    input = PermissionCreateInput(
                        permission_group_id=permission_group_id,
                        entity_type=entity_type,
                        operation=operation,
                    )
                    permission_inputs.append(input.to_dict())
        insert_if_data_exists(db_conn, get_permissions_table(), permission_inputs)

    @classmethod
    def _query_user_row(cls, db_conn: Connection, offset: int, page_size: int) -> list[Row]:
        """
        Query all user rows with pagination.
        """
        users_table = Tables.get_users_table()
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

    @classmethod
    def create_user_self_roles_and_permissions(cls, db_conn: Connection) -> None:
        """
        Migrate user data to roles and permissions.
        All users have a default self role and permissions.
        """
        offset = 0
        page_size = 1000
        while True:
            rows = cls._query_user_row(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            role_name_user_id_map = cls._create_self_roles(db_conn, rows)
            role_rows = query_role_rows_by_name(db_conn, list(role_name_user_id_map.keys()))
            role_id_user_id_map: dict[uuid.UUID, uuid.UUID] = {
                row.id: role_name_user_id_map[row.name] for row in role_rows
            }
            cls._create_permission_groups(db_conn, role_id_user_id_map)
            str_user_ids = [str(user_id) for user_id in role_id_user_id_map.values()]
            permission_group_ids = query_permission_groups_by_scope_ids(db_conn, str_user_ids)
            cls._create_permissions(db_conn, permission_group_ids)


class RoleMapper:
    @classmethod
    def _create_user_roles(
        cls, db_conn: Connection, role_id_user_id_map: Mapping[uuid.UUID, uuid.UUID]
    ) -> None:
        user_roles_table = get_user_roles_table()
        user_role_inputs: list[dict[str, Any]] = []
        for role_id, user_id in role_id_user_id_map.items():
            user_role_input = UserRoleCreateInput(user_id=user_id, role_id=role_id)
            user_role_inputs.append(user_role_input.to_dict())
        insert_if_data_exists(db_conn, user_roles_table, user_role_inputs)

    @classmethod
    def _query_user_row(cls, db_conn: Connection, offset: int, page_size: int) -> list[Row]:
        """
        Query all user rows with pagination.
        """
        users_table = Tables.get_users_table()
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

    @classmethod
    def map_users_to_roles(cls, db_conn: Connection) -> None:
        """
        Map users to their self roles.
        """
        offset = 0
        page_size = 1000
        while True:
            rows = cls._query_user_row(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            role_name_user_id_map: dict[str, uuid.UUID] = {}
            for row in rows:
                data = UserData.from_row(row)
                role_input = get_user_self_role_creation_input(data)
                role_name_user_id_map[role_input.name] = data.id

            role_rows = query_role_rows_by_name(db_conn, list(role_name_user_id_map.keys()))
            role_id_user_id_map: dict[uuid.UUID, uuid.UUID] = {
                row.id: role_name_user_id_map[row.name] for row in role_rows
            }
            cls._create_user_roles(db_conn, role_id_user_id_map)


def upgrade() -> None:
    conn = op.get_bind()
    RoleCreator.create_user_self_roles_and_permissions(conn)
    RoleMapper.map_users_to_roles(conn)


def downgrade() -> None:
    pass
