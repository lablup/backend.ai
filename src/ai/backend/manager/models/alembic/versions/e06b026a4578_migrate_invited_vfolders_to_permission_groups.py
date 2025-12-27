"""migrate invited vfolders to permission groups

Revision ID: e06b026a4578
Revises: b0fb0eb6b6bc
Create Date: 2025-12-04 16:42:17.153498

"""

import enum
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migration.enums import RoleSource, ScopeType
from ai.backend.manager.models.rbac_models.migration.models import (
    get_permission_groups_table,
    get_roles_table,
    get_user_roles_table,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    PermissionGroupCreateInput,
)
from ai.backend.manager.models.rbac_models.migration.utils import (
    insert_skip_on_conflict,
)
from ai.backend.manager.models.rbac_models.migration.vfolder import (
    VFolderPermission,
)

# revision identifiers, used by Alembic.
revision = "e06b026a4578"
down_revision = "b0fb0eb6b6bc"
branch_labels = None
depends_on = None

mapper_registry = registry(metadata=metadata)


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
    def get_vfolder_permissions_table() -> sa.Table:
        vfolder_permissions_table = sa.Table(
            "vfolder_permissions",
            mapper_registry.metadata,
            IDColumn("id"),
            sa.Column(
                "permission",
                EnumValueType(VFolderPermission),
                default=VFolderPermission.READ_WRITE,
                nullable=False,
            ),
            sa.Column(
                "vfolder",
                GUID,
                sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=False),
            extend_existing=True,
        )
        return vfolder_permissions_table

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


class PermissionCreator:
    @classmethod
    def add_unique_constraint_to_permission_groups_role_id_scope_id(cls) -> None:
        permission_groups_table = get_permission_groups_table()
        op.create_unique_constraint(
            "uq_permission_groups_role_id_scope_id",
            permission_groups_table.name,
            ["role_id", "scope_id", "scope_type"],
        )

    @classmethod
    def drop_unique_constraint_from_permission_groups_role_id_scope_id(cls) -> None:
        permission_groups_table = get_permission_groups_table()
        op.drop_constraint(
            "uq_permission_groups_role_id_scope_id",
            permission_groups_table.name,
            type_="unique",
        )

    @classmethod
    def _query_vfolder_permissions(
        cls,
        db_conn: Connection,
        offset: int,
        page_size: int,
    ) -> list[Row]:
        vfolder_permissions_table = Tables.get_vfolder_permissions_table()

        users_table = Tables.get_users_table()
        user_roles_table = get_user_roles_table()
        roles_table = get_roles_table()
        stmt = (
            sa.select(
                vfolder_permissions_table.c.user.label("user_id"),
                roles_table.c.id.label("role_id"),
            )
            .select_from(
                sa.join(
                    vfolder_permissions_table,
                    users_table,
                    vfolder_permissions_table.c.user == users_table.c.uuid,
                )
                .join(
                    user_roles_table,
                    user_roles_table.c.user_id == users_table.c.uuid,
                )
                .join(
                    roles_table,
                    roles_table.c.id == user_roles_table.c.role_id,
                )
            )
            .where(roles_table.c.source == RoleSource.SYSTEM)
            .offset(offset)
            .limit(page_size)
        )
        return db_conn.execute(stmt).all()

    @classmethod
    def _invitiee_user_to_permission_group_input(
        cls,
        role_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> PermissionGroupCreateInput:
        permission_group_input = PermissionGroupCreateInput(
            role_id=role_id,
            scope_type=ScopeType.USER,
            scope_id=str(user_id),
        )
        return permission_group_input

    @classmethod
    def add_vfolder_permissions_as_permission_groups(cls, db_conn: Connection) -> None:
        permission_groups_table = get_permission_groups_table()

        offset = 0
        page_size = 100
        while True:
            vp_rows = cls._query_vfolder_permissions(db_conn, offset, page_size)
            offset += page_size
            if not vp_rows:
                break
            permission_group_inputs: list[PermissionGroupCreateInput] = []
            for row in vp_rows:
                input = cls._invitiee_user_to_permission_group_input(
                    role_id=row.role_id,
                    user_id=row.user_id,
                )
                permission_group_inputs.append(input)

            insert_skip_on_conflict(db_conn, permission_groups_table, permission_group_inputs)


def upgrade() -> None:
    PermissionCreator.add_unique_constraint_to_permission_groups_role_id_scope_id()
    conn = op.get_bind()
    PermissionCreator.add_vfolder_permissions_as_permission_groups(conn)
    PermissionCreator.drop_unique_constraint_from_permission_groups_role_id_scope_id()


def downgrade() -> None:
    pass
