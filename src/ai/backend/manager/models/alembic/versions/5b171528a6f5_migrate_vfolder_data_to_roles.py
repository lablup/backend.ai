"""migrate vfolder data to roles

Revision ID: 5b171528a6f5
Revises: a4d56e86d9ee
Create Date: 2025-08-07 23:53:34.718192

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import registry

from ai.backend.common.defs import MODEL_VFOLDER_LENGTH_LIMIT
from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migration.models import (
    get_roles_table,
    get_scope_permissions_table,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    PermissionCreateInputGroup,
)
from ai.backend.manager.models.rbac_models.migration.utils import insert_from_create_input_group
from ai.backend.manager.models.rbac_models.migration.vfolder import (
    RoleData,
    ScopeData,
    VFolderData,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionData,
    add_vfolder_scope_permissions_to_role,
    map_vfolder_entity_to_scope,
    map_vfolder_permission_data_to_scope,
)

# revision identifiers, used by Alembic.
revision = "5b171528a6f5"
down_revision = "a4d56e86d9ee"
branch_labels = None
depends_on = None


mapper_registry = registry(metadata=metadata)


def _get_vfolders_table() -> sa.Table:
    vfolders_table = sa.Table(
        "vfolders",
        mapper_registry.metadata,
        IDColumn("id"),
        sa.Column("name", sa.String(length=MODEL_VFOLDER_LENGTH_LIMIT), nullable=False, index=True),
        sa.Column(
            "ownership_type",
            EnumValueType(VFolderOwnershipType),
            default=VFolderOwnershipType.USER,
            nullable=False,
            index=True,
        ),
        sa.Column("user", GUID, nullable=True),  # owner if user vfolder
        sa.Column("group", GUID, nullable=True),  # owner if project vfolder
        extend_existing=True,
    )
    return vfolders_table


def _get_vfolder_permissions_table() -> sa.Table:
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


def _define_cte() -> sa.sql.Select:
    """
    Define a CTE to get all roles that need vfolder permissions.
    Join roles with scope permissions to get the first scope permissions row for each role.
    Assumes that all scope_id of scope permissions for a role are the same.
    """
    roles_table = get_roles_table()
    scope_permissions_table = get_scope_permissions_table()

    roles_batch = (
        sa.select(
            roles_table.c.id,
            roles_table.c.source,
            scope_permissions_table.c.scope_id,
            scope_permissions_table.c.scope_type,
            sa.func.row_number()
            .over(
                partition_by=scope_permissions_table.c.role_id,
                order_by=scope_permissions_table.c.id,
            )
            .label("row_num"),
        )
        .select_from(
            sa.join(
                roles_table,
                scope_permissions_table,
                roles_table.c.id == scope_permissions_table.c.role_id,
            )
        )
        .cte("roles_batch")
    )

    return roles_batch


def _query_roles(db_conn: Connection, cte: sa.sql.Select, offset: int, page_size: int) -> list[Row]:
    """
    Query to get system roles that need vfolder permissions.
    """
    stmt = (
        sa.select(cte).where(cte.c.row_num == 1).offset(offset).limit(page_size).order_by(cte.c.id)
    )

    return db_conn.execute(stmt).all()


def _add_vfolder_entity_type_permission_to_roles(db_conn: Connection) -> None:
    """
    Add scope permissions for vfolder entity type to roles.
    """
    roles_batch_cte = _define_cte()
    offset = 0
    page_size = 1000

    while True:
        rows = _query_roles(db_conn, roles_batch_cte, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            input_data = add_vfolder_scope_permissions_to_role(
                RoleData.from_row(row),
                ScopeData.from_row(row),
            )
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def _query_vfolder_rows(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query to get all vfolders.
    """
    vfolders_table = _get_vfolders_table()
    query = (
        sa.select(
            vfolders_table.c.id,
            vfolders_table.c.ownership_type,
            vfolders_table.c.user,
            vfolders_table.c.group,
        )
        .offset(offset)
        .limit(page_size)
        .order_by(vfolders_table.c.id)
    )
    return db_conn.execute(query).all()


def _map_vfolder_rows_to_scope(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        rows = _query_vfolder_rows(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for vfolder in rows:
            data = VFolderData(
                id=vfolder.id,
                ownership_type=vfolder.ownership_type,
                user_id=vfolder.user,
                group_id=vfolder.group,
            )
            input_data = map_vfolder_entity_to_scope(data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def _query_vfolder_permission_rows(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query to get all vfolder permissions.
    """
    vfolder_permissions_table = _get_vfolder_permissions_table()
    query = (
        sa.select(
            vfolder_permissions_table.c.vfolder,
            vfolder_permissions_table.c.user,
            vfolder_permissions_table.c.permission,
        )
        .offset(offset)
        .limit(page_size)
        .order_by(vfolder_permissions_table.c.id)
    )
    return db_conn.execute(query).all()


def _map_vfolder_permission_rows_to_scope(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        rows = _query_vfolder_permission_rows(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for vf_perm in rows:
            data = VFolderPermissionData(
                vfolder_id=vf_perm.vfolder,
                user_id=vf_perm.user,
                mount_permission=vf_perm.permission,
            )
            input_data = map_vfolder_permission_data_to_scope(data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def upgrade() -> None:
    conn = op.get_bind()
    _add_vfolder_entity_type_permission_to_roles(conn)

    _map_vfolder_rows_to_scope(conn)

    _map_vfolder_permission_rows_to_scope(conn)


def downgrade() -> None:
    pass
