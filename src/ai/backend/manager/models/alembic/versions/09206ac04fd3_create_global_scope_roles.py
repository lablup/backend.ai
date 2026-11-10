"""create global roles

Revision ID: 09206ac04fd3
Revises: de1032a11cca
Create Date: 2025-09-22 19:44:13.067238

"""

import enum
import uuid
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.models.base import EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.enums import (
    EntityType,
    OperationType,
)
from ai.backend.manager.models.rbac_models.migration.models import (
    get_user_roles_table,
    mapper_registry,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    UserRoleCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    get_monitor_role_creation_input,
    get_superadmin_role_creation_input,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    PermissionUpdateUtil,
    insert_skip_on_conflict,
)

# revision identifiers, used by Alembic.
revision = "09206ac04fd3"
down_revision = "de1032a11cca"
branch_labels = None
depends_on = None

# Metadata local to this revision so that the table snapshots below cannot be
# altered by definitions living in other revisions.
_local_metadata = sa.MetaData()


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
        return sa.Table(
            "users",
            mapper_registry.metadata,
            IDColumn("uuid"),
            sa.Column("username", sa.String(length=64), unique=True),
            sa.Column("role", EnumValueType(UserRole), default=UserRole.USER),
            extend_existing=True,
        )

    @staticmethod
    def get_roles_table() -> sa.Table:
        """Snapshot of the ``roles`` schema at this revision: ``state`` was renamed to
        ``status`` by 643deb439458 and ``source`` was added by 42feff246198."""
        return sa.Table(
            "roles",
            _local_metadata,
            IDColumn(),
            sa.Column("name", sa.String(64), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("status", sa.VARCHAR(16), nullable=False, server_default="active"),
            sa.Column("source", sa.VARCHAR(16), nullable=False, server_default="system"),
            extend_existing=True,
        )


def _get_or_create_role(db_conn: Connection, name: str, source: str, status: str) -> uuid.UUID:
    roles_table = Tables.get_roles_table()
    role_id: uuid.UUID | None = db_conn.scalar(
        sa.select(roles_table.c.id).where(
            sa.and_(
                roles_table.c.name == name,
                roles_table.c.source == source,
            )
        )
    )
    if role_id is not None:
        return role_id
    created_id: uuid.UUID = db_conn.execute(
        sa.insert(roles_table)
        .values({"name": name, "source": source, "status": status})
        .returning(roles_table.c.id)
    ).scalar_one()
    return created_id


class RoleCreator:
    @classmethod
    def _create_superadmin_role(cls, db_conn: Connection) -> uuid.UUID:
        role_input = get_superadmin_role_creation_input()
        role_id = _get_or_create_role(
            db_conn, role_input.name, role_input.source, role_input.status
        )
        permission_group_id, exist = PermissionUpdateUtil.get_or_create_global_permission_group(
            db_conn, role_id
        )
        if not exist:
            PermissionUpdateUtil.create_permissions(
                db_conn, permission_group_id, ENTITY_TYPES, OperationType.admin_operations()
            )
        return role_id

    @classmethod
    def _create_monitor_role(cls, db_conn: Connection) -> uuid.UUID:
        role_input = get_monitor_role_creation_input()
        role_id = _get_or_create_role(
            db_conn, role_input.name, role_input.source, role_input.status
        )
        permission_group_id, exist = PermissionUpdateUtil.get_or_create_global_permission_group(
            db_conn, role_id
        )
        if not exist:
            PermissionUpdateUtil.create_permissions(
                db_conn, permission_group_id, ENTITY_TYPES, OperationType.monitor_operations()
            )
        return role_id

    @classmethod
    def _query_user_row_by_role(
        cls, db_conn: Connection, role: UserRole, offset: int, page_size: int
    ) -> Sequence[Row[Any]]:
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
