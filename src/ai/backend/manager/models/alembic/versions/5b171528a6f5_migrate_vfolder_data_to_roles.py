"""migrate vfolder data to roles

Revision ID: 5b171528a6f5
Revises: e43125b98bba
Create Date: 2025-08-07 23:53:34.718192

"""

import uuid
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migration.enums import RoleSource
from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
    get_object_permissions_table,
    get_permission_groups_table,
    get_permissions_table,
    get_roles_table,
    get_user_roles_table,
)
from ai.backend.manager.models.rbac_models.migration.utils import insert_if_data_exists
from ai.backend.manager.models.rbac_models.migration.vfolder import (
    VFOLDER_ENTITY,
    VFolderOwnershipType,
    VFolderPermission,
    map_vfolder_entity_to_scope_id,
    role_source_to_operation,
    vfolder_mount_permission_to_operation,
)

# revision identifiers, used by Alembic.
revision = "5b171528a6f5"
down_revision = "e43125b98bba"
branch_labels = None
depends_on = None


mapper_registry = registry(metadata=metadata)


class Tables:
    @staticmethod
    def get_vfolder_table() -> sa.Table:
        vfolder_table = sa.Table(
            "vfolders",
            mapper_registry.metadata,
            IDColumn("id"),
            sa.Column(
                "ownership_type",
                EnumValueType(VFolderOwnershipType),
                nullable=False,
            ),
            sa.Column("user", GUID, nullable=True),
            sa.Column("group", GUID, nullable=True),
            sa.Column("domain_name", sa.String(255), nullable=False),
            extend_existing=True,
        )
        return vfolder_table

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


class PermissionCreator:
    @classmethod
    def _query_roles(cls, db_conn: Connection, offset: int, page_size: int) -> list[Row]:
        """
        Query to get system roles that need vfolder permissions.
        """
        roles_table = get_roles_table()
        permission_groups_table = get_permission_groups_table()
        j = sa.join(
            roles_table,
            permission_groups_table,
            roles_table.c.id == permission_groups_table.c.role_id,
        )
        stmt = (
            sa.select(
                roles_table.c.source.label("role_source"),
                permission_groups_table.c.id.label("permission_group_id"),
            )
            .select_from(j)
            .offset(offset)
            .limit(page_size)
            .order_by(roles_table.c.id)
        )

        return db_conn.execute(stmt).all()

    @classmethod
    def _query_vfolder_permission_rows_with_role(
        cls, db_conn: Connection, offset: int, page_size: int
    ) -> list[Row]:
        user_roles_table = get_user_roles_table()
        vfolder_permissions_table = Tables.get_vfolder_permissions_table()

        j = sa.join(
            vfolder_permissions_table,
            user_roles_table,
            vfolder_permissions_table.c.user == user_roles_table.c.user_id,
        )
        query = (
            sa.select(
                user_roles_table.c.role_id,
                vfolder_permissions_table.c.vfolder.label("vfolder_id"),
                vfolder_permissions_table.c.permission.label("mount_permission"),
            )
            .select_from(j)
            .offset(offset)
            .limit(page_size)
            .order_by(vfolder_permissions_table.c.id)
        )
        return db_conn.execute(query).all()

    @classmethod
    def _permission_inputs_to_permission_group(
        cls, role_source: RoleSource, permission_group_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        inputs: list[dict[str, Any]] = []
        operations = role_source_to_operation[role_source]
        for operation in operations:
            input = {
                "permission_group_id": permission_group_id,
                "entity_type": VFOLDER_ENTITY,
                "operation": str(operation),
            }
            inputs.append(input)
        return inputs

    @classmethod
    def add_vfolder_entity_type_permission_to_permission_groups(cls, db_conn: Connection) -> None:
        permissions_table = get_permissions_table()

        offset = 0
        page_size = 1000

        while True:
            rows = cls._query_roles(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            permission_inputs: list[dict[str, Any]] = []
            for row in rows:
                inputs = cls._permission_inputs_to_permission_group(
                    role_source=row.role_source,
                    permission_group_id=row.permission_group_id,
                )
                permission_inputs.extend(inputs)
            insert_if_data_exists(db_conn, permissions_table, permission_inputs)

    @classmethod
    def _vfolder_permission_to_object_permission_inputs(
        cls,
        role_id: uuid.UUID,
        vfolder_id: uuid.UUID,
        vfolder_mount_permission: VFolderPermission,
    ) -> list[dict[str, Any]]:
        inputs: list[dict[str, Any]] = []
        operations = vfolder_mount_permission_to_operation[vfolder_mount_permission]
        for operation in operations:
            input = {
                "role_id": role_id,
                "entity_type": VFOLDER_ENTITY,
                "entity_id": str(vfolder_id),
                "operation": operation,
            }
            inputs.append(input)
        return inputs

    @classmethod
    def add_vfolder_object_permissions(cls, db_conn: Connection) -> None:
        object_permissions_table = get_object_permissions_table()

        offset = 0
        page_size = 1000

        while True:
            rows = cls._query_vfolder_permission_rows_with_role(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            object_permission_inputs: list[dict[str, Any]] = []
            for vf_perm in rows:
                inputs = cls._vfolder_permission_to_object_permission_inputs(
                    role_id=vf_perm.role_id,
                    vfolder_id=vf_perm.vfolder_id,
                    vfolder_mount_permission=vf_perm.mount_permission,
                )
                object_permission_inputs.extend(inputs)
            insert_if_data_exists(db_conn, object_permissions_table, object_permission_inputs)


class EntityMapper:
    @classmethod
    def _query_vfolder_rows(cls, db_conn: Connection, offset: int, page_size: int) -> list[Row]:
        vfolder_table = Tables.get_vfolder_table()
        stmt = (
            sa.select(
                vfolder_table.c.id,
                vfolder_table.c.domain_name,
                vfolder_table.c.ownership_type,
                vfolder_table.c.user,
                vfolder_table.c.group,
            )
            .offset(offset)
            .limit(page_size)
            .order_by(vfolder_table.c.id)
        )
        return db_conn.execute(stmt).all()

    @classmethod
    def map_vfolder_entity_to_scope(cls, db_conn: Connection) -> None:
        association_scopes_entities_table = get_association_scopes_entities_table()
        offset = 0
        page_size = 1000

        while True:
            rows = cls._query_vfolder_rows(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            mapping_inputs: list[dict[str, Any]] = []
            for row in rows:
                domain_input = {
                    "entity_type": VFOLDER_ENTITY,
                    "entity_id": str(row.id),
                    "scope_type": "domain",
                    "scope_id": row.domain_name,
                }
                mapping_inputs.append(domain_input)
                scope_id = map_vfolder_entity_to_scope_id(
                    ownership_type=row.ownership_type,
                    user_id=row.user,
                    project_id=row.group,
                )
                if scope_id is not None:
                    input = {
                        "entity_type": VFOLDER_ENTITY,
                        "entity_id": str(row.id),
                        "scope_type": scope_id.scope_type,
                        "scope_id": scope_id.scope_id,
                    }
                    mapping_inputs.append(input)
            insert_if_data_exists(db_conn, association_scopes_entities_table, mapping_inputs)

    @classmethod
    def _query_vfolder_permissions_rows(
        cls, db_conn: Connection, offset: int, page_size: int
    ) -> list[Row]:
        vfolder_permissions_table = Tables.get_vfolder_permissions_table()
        stmt = (
            sa.select(
                vfolder_permissions_table.c.vfolder.label("vfolder_id"),
                vfolder_permissions_table.c.user.label("user_id"),
            )
            .offset(offset)
            .limit(page_size)
            .order_by(vfolder_permissions_table.c.id)
        )
        return db_conn.execute(stmt).all()

    @classmethod
    def map_vfolder_permission_to_scope(cls, db_conn: Connection) -> None:
        association_scopes_entities_table = get_association_scopes_entities_table()
        offset = 0
        page_size = 1000

        while True:
            rows = cls._query_vfolder_permissions_rows(db_conn, offset, page_size)
            offset += page_size
            if not rows:
                break
            mapping_inputs: list[dict[str, Any]] = []
            for row in rows:
                scope_id = map_vfolder_entity_to_scope_id(
                    ownership_type=VFolderOwnershipType.USER,
                    user_id=row.user_id,
                    project_id=None,
                )
                if scope_id is not None:
                    mapping_input = {
                        "entity_type": VFOLDER_ENTITY,
                        "entity_id": str(row.vfolder_id),
                        "scope_type": scope_id.scope_type,
                        "scope_id": scope_id.scope_id,
                    }
                    mapping_inputs.append(mapping_input)
            insert_if_data_exists(db_conn, association_scopes_entities_table, mapping_inputs)


def upgrade() -> None:
    op.execute("""
        ALTER TABLE association_scopes_entities
        DROP CONSTRAINT IF EXISTS uq_scope_id_entity_id
    """)
    conn = op.get_bind()
    PermissionCreator.add_vfolder_entity_type_permission_to_permission_groups(conn)
    PermissionCreator.add_vfolder_object_permissions(conn)

    EntityMapper.map_vfolder_entity_to_scope(conn)
    EntityMapper.map_vfolder_permission_to_scope(conn)


def downgrade() -> None:
    pass
