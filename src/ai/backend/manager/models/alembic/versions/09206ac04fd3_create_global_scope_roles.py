"""create global roles

Revision ID: 09206ac04fd3
Revises: 08c1867e266e
Create Date: 2025-09-22 19:44:13.067238

"""

import enum
import uuid
from collections.abc import Iterable
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.models.base import EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.domain import EntityType
from ai.backend.manager.models.rbac_models.migration.enums import (
    GLOBAL_SCOPE_ID,
    OperationType,
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
    get_monitor_role_creation_input,
    get_superadmin_role_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_if_data_exists,
    query_role_rows_by_name,
)

# revision identifiers, used by Alembic.
revision = "09206ac04fd3"
down_revision = "08c1867e266e"
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


ENTITY_TYPES = {
    EntityType.USER,
    EntityType.PROJECT,
    EntityType.DOMAIN,
    EntityType.VFOLDER,
}


class Tables:
    @staticmethod
    def get_users_table() -> sa.Table:
        users_table = sa.Table(
            "users",
            mapper_registry.metadata,
            IDColumn("uuid"),
            sa.Column("username", sa.String(length=64), unique=True),
            sa.Column("role", EnumValueType(UserRole), default=UserRole.USER),
            extend_existing=True,
        )
        return users_table


class RoleCreator:
    @classmethod
    def _create_permission_group(cls, db_conn: Connection, role_id: uuid.UUID) -> uuid.UUID:
        permission_groups_table = get_permission_groups_table()
        input = (
            PermissionGroupCreateInput(
                role_id=role_id,
                scope_type=ScopeType.GLOBAL,
                scope_id=GLOBAL_SCOPE_ID,
            )
        ).to_dict()
        insert_if_data_exists(
            db_conn,
            permission_groups_table,
            [input],
        )

        permission_group_row = db_conn.execute(
            sa.select(permission_groups_table.c.id).where(
                permission_groups_table.c.role_id == role_id,
            )
        )
        return permission_group_row.scalar_one()

    @classmethod
    def _create_permissions(
        cls,
        db_conn: Connection,
        permission_group_id: uuid.UUID,
        operations: Iterable[OperationType],
    ) -> None:
        permission_inputs: list[dict[str, Any]] = []
        for entity_type in ENTITY_TYPES:
            for operation in operations:
                input = PermissionCreateInput(
                    permission_group_id=permission_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                permission_inputs.append(input.to_dict())
        insert_if_data_exists(db_conn, get_permissions_table(), permission_inputs)

    @classmethod
    def _create_superadmin_role(cls, db_conn: Connection) -> uuid.UUID:
        role_input = get_superadmin_role_creation_input()
        insert_if_data_exists(db_conn, get_roles_table(), [role_input.to_dict()])
        role_name = role_input.name
        role_row = query_role_rows_by_name(db_conn, [role_name])
        role_id = role_row[0].id
        permission_group_id = cls._create_permission_group(db_conn, role_id)
        cls._create_permissions(db_conn, permission_group_id, OperationType.admin_operations())
        return role_id

    @classmethod
    def _create_monitor_role(cls, db_conn: Connection) -> uuid.UUID:
        role_input = get_monitor_role_creation_input()
        insert_if_data_exists(db_conn, get_roles_table(), [role_input.to_dict()])
        role_name = role_input.name
        role_row = query_role_rows_by_name(db_conn, [role_name])
        role_id = role_row[0].id
        permission_group_id = cls._create_permission_group(db_conn, role_id)
        cls._create_permissions(db_conn, permission_group_id, OperationType.monitor_operations())
        return role_id

    @classmethod
    def _query_user_row_by_role(
        cls, db_conn: Connection, role: UserRole, offset: int, page_size: int
    ) -> list[Row]:
        """
        Query all user rows with pagination.
        """
        users_table = Tables.get_users_table()
        user_query = (
            sa.select(
                users_table.c.uuid,
                users_table.c.username,
                users_table.c.role,
            )
            .offset(offset)
            .limit(page_size)
            .where(users_table.c.role == role)
            .order_by(users_table.c.uuid)
        )
        return db_conn.execute(user_query).all()

    @classmethod
    def _map_role_to_users(
        cls, db_conn: Connection, user_role: UserRole, role_id: uuid.UUID
    ) -> None:
        user_roles_table = get_user_roles_table()
        offset = 0
        page_size = 1000
        while True:
            rows = cls._query_user_row_by_role(db_conn, user_role, offset, page_size)
            offset += page_size
            if not rows:
                break

            user_role_inputs: list[dict[str, Any]] = [
                UserRoleCreateInput(user_id=row.uuid, role_id=role_id).to_dict() for row in rows
            ]
            insert_if_data_exists(db_conn, user_roles_table, user_role_inputs)

    @classmethod
    def create_and_map_superadmin_role(cls, db_conn: Connection) -> None:
        superadmin_role_id = cls._create_superadmin_role(db_conn)
        cls._map_role_to_users(db_conn, UserRole.SUPERADMIN, superadmin_role_id)

    @classmethod
    def create_and_map_monitor_role(cls, db_conn: Connection) -> None:
        monitor_role_id = cls._create_monitor_role(db_conn)
        cls._map_role_to_users(db_conn, UserRole.MONITOR, monitor_role_id)


def upgrade() -> None:
    conn = op.get_bind()
    RoleCreator.create_and_map_superadmin_role(conn)
    RoleCreator.create_and_map_monitor_role(conn)


def downgrade() -> None:
    pass
