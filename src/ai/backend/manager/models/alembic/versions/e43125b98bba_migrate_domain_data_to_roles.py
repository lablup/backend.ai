"""migrate domain data to roles

Revision ID: e43125b98bba
Revises: 430b1631804d
Create Date: 2025-08-12 15:38:26.989485

"""

import enum
import uuid
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.models.base import EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.domain import (
    ADMIN_ACCESSIBLE_ENTITY_TYPES,
    MEMBER_ACCESSIBLE_ENTITY_TYPES,
    DomainData,
    get_domain_admin_role_creation_input,
    get_domain_member_role_creation_input,
)
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
    PermissionGroupCreateInput,
    UserRoleCreateInput,
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

    @staticmethod
    def get_groups_table() -> sa.Table:
        groups_table = sa.Table(
            "groups",
            mapper_registry.metadata,
            IDColumn(),
            sa.Column(
                "domain_name",
                sa.String(length=64),
                sa.ForeignKey("domains.name", onupdate="CASCADE", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            extend_existing=True,
        )
        return groups_table

    @staticmethod
    def get_domains_table() -> sa.Table:
        domains_table = sa.Table(
            "domains",
            mapper_registry.metadata,
            sa.Column("name", sa.Unicode(length=64), primary_key=True),
            extend_existing=True,
        )
        return domains_table


class RoleCreator:
    @classmethod
    def _create_admin_roles(cls, db_conn: Connection, rows: Sequence[Row]) -> dict[str, str]:
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

    @classmethod
    def _create_member_roles(cls, db_conn: Connection, rows: Sequence[Row]) -> dict[str, str]:
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

    @classmethod
    def _create_permission_groups(
        cls, db_conn: Connection, role_id_domain_name_map: Mapping[uuid.UUID, str]
    ) -> None:
        permission_groups_table = get_permission_groups_table()
        permission_group_inputs: list[dict[str, Any]] = []
        for role_id, domain_name in role_id_domain_name_map.items():
            input = PermissionGroupCreateInput(
                role_id=role_id,
                scope_type=ScopeType.DOMAIN,
                scope_id=domain_name,
            )
            permission_group_inputs.append(input.to_dict())
        insert_if_data_exists(db_conn, permission_groups_table, permission_group_inputs)

    @classmethod
    def _create_admin_permissions(
        cls, db_conn: Connection, permission_group_ids: Iterable[uuid.UUID]
    ) -> None:
        permission_inputs: list[dict[str, Any]] = []
        for permission_group_id in permission_group_ids:
            for entity_type in ADMIN_ACCESSIBLE_ENTITY_TYPES:
                for operation in OperationType.admin_operations():
                    input = PermissionCreateInput(
                        permission_group_id=permission_group_id,
                        entity_type=entity_type,
                        operation=operation,
                    )
                    permission_inputs.append(input.to_dict())
        insert_if_data_exists(db_conn, get_permissions_table(), permission_inputs)

    @classmethod
    def _create_member_permissions(
        cls, db_conn: Connection, permission_group_ids: Iterable[uuid.UUID]
    ) -> None:
        scope_permission_inputs: list[dict[str, Any]] = []
        for permission_group_id in permission_group_ids:
            for entity_type in MEMBER_ACCESSIBLE_ENTITY_TYPES:
                for operation in OperationType.member_operations():
                    input = PermissionCreateInput(
                        permission_group_id=permission_group_id,
                        entity_type=entity_type,
                        operation=operation,
                    )
                    scope_permission_inputs.append(input.to_dict())
        insert_if_data_exists(db_conn, get_permissions_table(), scope_permission_inputs)

    @classmethod
    def _create_domain_admin_roles_and_permissions(
        cls, db_conn: Connection, rows: Sequence[Row]
    ) -> None:
        role_name_domain_name_map = cls._create_admin_roles(db_conn, rows)
        role_rows = query_role_rows_by_name(db_conn, list(role_name_domain_name_map.keys()))
        role_id_domain_name_map: dict[uuid.UUID, str] = {
            row.id: role_name_domain_name_map[row.name] for row in role_rows
        }
        cls._create_permission_groups(db_conn, role_id_domain_name_map)
        permission_group_ids = query_permission_groups_by_scope_ids(
            db_conn, list(role_id_domain_name_map.values())
        )
        cls._create_admin_permissions(db_conn, permission_group_ids)

    @classmethod
    def _create_domain_member_roles_and_permissions(
        cls, db_conn: Connection, rows: Sequence[Row]
    ) -> None:
        role_name_domain_name_map = cls._create_member_roles(db_conn, rows)
        role_rows = query_role_rows_by_name(db_conn, list(role_name_domain_name_map.keys()))
        role_id_domain_name_map: dict[uuid.UUID, str] = {
            row.id: role_name_domain_name_map[row.name] for row in role_rows
        }
        cls._create_permission_groups(db_conn, role_id_domain_name_map)
        permission_group_ids = query_permission_groups_by_scope_ids(
            db_conn, list(role_id_domain_name_map.values())
        )
        cls._create_member_permissions(db_conn, permission_group_ids)

    @classmethod
    def _query_domain_row(cls, db_conn: Connection, offset: int, page_size: int) -> list[Row]:
        """
        Query all domain rows with pagination.
        """
        domains_table = Tables.get_domains_table()
        domain_query = (
            sa.select(domains_table.c.name)
            .offset(offset)
            .limit(page_size)
            .order_by(domains_table.c.name)
        )
        return db_conn.execute(domain_query).all()

    @classmethod
    def create_domain_roles_and_permissions(cls, db_conn: Connection) -> None:
        """
        Migrate domain data to roles and permissions.
        All domains have a default admin role and a member role.
        """
        offset = 0
        page_size = 1000
        while True:
            rows = cls._query_domain_row(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            cls._create_domain_admin_roles_and_permissions(db_conn, rows)
            cls._create_domain_member_roles_and_permissions(db_conn, rows)


class RoleMapper:
    @classmethod
    def _query_role_with_user(
        cls, db_conn: Connection, offset: int, page_size: int, *, is_admin: bool
    ) -> list[Row]:
        users_table = Tables.get_users_table()
        roles_table = get_roles_table()
        permission_groups_table = get_permission_groups_table()

        if is_admin:
            condition = sa.and_(
                roles_table.c.source == RoleSource.SYSTEM,
                users_table.c.role == UserRole.ADMIN,
            )
        else:
            condition = sa.and_(
                roles_table.c.source == RoleSource.CUSTOM,
                users_table.c.role == UserRole.USER,
            )

        stmt = (
            sa.select(
                roles_table.c.id.label("role_id"),
                permission_groups_table.c.scope_id,
                users_table.c.uuid.label("user_id"),
            )
            .select_from(
                sa.join(
                    roles_table,
                    permission_groups_table,
                    roles_table.c.id == permission_groups_table.c.role_id,
                ).join(
                    users_table,
                    permission_groups_table.c.scope_id == users_table.c.domain_name,
                )
            )
            .where(condition)
            .offset(offset)
            .limit(page_size)
            .order_by(users_table.c.uuid)
        )
        return db_conn.execute(stmt).all()

    @classmethod
    def _map_admin_users_to_domain(cls, db_conn: Connection) -> None:
        user_roles_table = get_user_roles_table()
        association_table = get_association_scopes_entities_table()

        offset = 0
        page_size = 1000

        while True:
            rows = cls._query_role_with_user(db_conn, offset, page_size, is_admin=True)
            offset += page_size
            if not rows:
                break
            user_role_inputs: list[dict[str, Any]] = []
            association_inputs: list[dict[str, Any]] = []
            for row in rows:
                user_role_input = UserRoleCreateInput(user_id=row.user_id, role_id=row.role_id)
                user_role_inputs.append(user_role_input.to_dict())

                association_input = AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.DOMAIN.to_original(),
                        scope_id=row.scope_id,
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.USER.to_original(),
                        entity_id=str(row.user_id),
                    ),
                )
                association_inputs.append(association_input.to_dict())
            insert_if_data_exists(db_conn, user_roles_table, user_role_inputs)
            insert_if_data_exists(db_conn, association_table, association_inputs)

    @classmethod
    def _map_member_users_to_domain(cls, db_conn: Connection) -> None:
        user_roles_table = get_user_roles_table()
        association_table = get_association_scopes_entities_table()

        offset = 0
        page_size = 1000

        while True:
            rows = cls._query_role_with_user(db_conn, offset, page_size, is_admin=False)
            offset += page_size
            if not rows:
                break
            user_role_inputs: list[dict[str, Any]] = []
            association_inputs: list[dict[str, Any]] = []
            for row in rows:
                input = UserRoleCreateInput(user_id=row.user_id, role_id=row.role_id)
                user_role_inputs.append(input.to_dict())

                association_input = AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.DOMAIN.to_original(),
                        scope_id=row.scope_id,
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.USER.to_original(),
                        entity_id=str(row.user_id),
                    ),
                )
                association_inputs.append(association_input.to_dict())
            insert_if_data_exists(db_conn, user_roles_table, user_role_inputs)
            insert_if_data_exists(db_conn, association_table, association_inputs)

    @classmethod
    def map_users_to_domain(cls, db_conn: Connection) -> None:
        cls._map_admin_users_to_domain(db_conn)
        cls._map_member_users_to_domain(db_conn)

    @classmethod
    def _query_project_row(cls, db_conn: Connection, offset: int, page_size: int) -> list[Row]:
        """
        Query all project rows with pagination.
        """
        groups_table = Tables.get_groups_table()
        project_query = (
            sa.select(groups_table.c.id, groups_table.c.domain_name)
            .offset(offset)
            .limit(page_size)
            .order_by(groups_table.c.id)
        )
        return db_conn.execute(project_query).all()

    @classmethod
    def map_projects_to_domain(cls, db_conn: Connection) -> None:
        association_table = get_association_scopes_entities_table()

        offset = 0
        page_size = 1000

        while True:
            rows = cls._query_project_row(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            association_inputs: list[dict[str, Any]] = []
            for row in rows:
                association_input = AssociationScopesEntitiesCreateInput(
                    scope_id=ScopeId(
                        scope_type=ScopeType.DOMAIN.to_original(),
                        scope_id=row.domain_name,
                    ),
                    object_id=ObjectId(
                        entity_type=EntityType.PROJECT.to_original(),
                        entity_id=str(row.id),
                    ),
                )
                association_inputs.append(association_input.to_dict())
            insert_if_data_exists(db_conn, association_table, association_inputs)


def upgrade() -> None:
    op.execute("""
        ALTER TABLE association_scopes_entities
        DROP CONSTRAINT IF EXISTS uq_scope_id_entity_id
    """)
    conn = op.get_bind()
    RoleCreator.create_domain_roles_and_permissions(conn)
    RoleMapper.map_users_to_domain(conn)
    RoleMapper.map_projects_to_domain(conn)


def downgrade() -> None:
    pass
