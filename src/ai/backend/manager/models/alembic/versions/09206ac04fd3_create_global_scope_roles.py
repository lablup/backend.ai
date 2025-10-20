"""create global roles

Revision ID: 09206ac04fd3
Revises: de1032a11cca
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
    GLOBAL_SCOPE_ID,
    PermissionCreateInput,
    PermissionGroupCreateInput,
    RoleCreateInput,
    UserRoleCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    get_monitor_role_creation_input,
    get_superadmin_role_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_and_returning_id,
    insert_if_data_exists,
    insert_skip_on_conflict,
)

# revision identifiers, used by Alembic.
revision = "09206ac04fd3"
down_revision = "de1032a11cca"
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
    def _get_or_create_role(cls, db_conn: Connection, role_input: RoleCreateInput) -> uuid.UUID:
        roles_table = get_roles_table()
        result = db_conn.execute(
            sa.select(roles_table).where(
                sa.and_(
                    roles_table.c.name == role_input.name,
                    roles_table.c.source == role_input.source,
                )
            )
        )
        role_row = result.fetchone()
        if role_row is not None:
            return role_row.id
        else:
            role_id = insert_and_returning_id(
                db_conn,
                roles_table,
                role_input.to_dict(),
            )
            return role_id

    @classmethod
    def _get_or_create_global_permission_group(
        cls, db_conn: Connection, role_id: uuid.UUID
    ) -> tuple[uuid.UUID, bool]:
        permission_groups_table = get_permission_groups_table()
        result = db_conn.execute(
            sa.select(permission_groups_table.c.id).where(
                sa.and_(
                    permission_groups_table.c.role_id == role_id,
                    permission_groups_table.c.scope_id == GLOBAL_SCOPE_ID,
                )
            )
        )
        permission_group_row = result.fetchone()
        if permission_group_row is not None:
            return permission_group_row.id, True
        else:
            input = (
                PermissionGroupCreateInput(
                    role_id=role_id,
                    scope_type=ScopeType.GLOBAL,
                    scope_id=GLOBAL_SCOPE_ID,
                )
            ).to_dict()
            permission_group_id = insert_and_returning_id(
                db_conn,
                permission_groups_table,
                input,
            )
            return permission_group_id, False

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
        role_id = cls._get_or_create_role(db_conn, role_input)
        permission_group_id, exist = cls._get_or_create_global_permission_group(db_conn, role_id)
        if not exist:
            cls._create_permissions(db_conn, permission_group_id, OperationType.admin_operations())
        return role_id

    @classmethod
    def _create_monitor_role(cls, db_conn: Connection) -> uuid.UUID:
        role_input = get_monitor_role_creation_input()
        role_id = cls._get_or_create_role(db_conn, role_input)
        permission_group_id, exist = cls._get_or_create_global_permission_group(db_conn, role_id)
        if not exist:
            cls._create_permissions(
                db_conn, permission_group_id, OperationType.monitor_operations()
            )
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
            insert_skip_on_conflict(db_conn, user_roles_table, user_role_inputs)

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
