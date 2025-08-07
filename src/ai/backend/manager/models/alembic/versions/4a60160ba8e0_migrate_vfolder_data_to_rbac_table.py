"""migrate vfolder data to rbac table

Revision ID: 4a60160ba8e0
Revises: a4d56e86d9ee
Create Date: 2025-07-30 14:44:14.346887

"""

import enum
import uuid
from collections.abc import Collection
from typing import Any, Optional

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Connection
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import registry

from ai.backend.common.defs import MODEL_VFOLDER_LENGTH_LIMIT
from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migrate.types import (
    PermissionCreateInputGroup,
    is_admin_role,
)
from ai.backend.manager.models.rbac_models.migrate.vfolder import (
    ProjectVFolderData,
    UserVFolderData,
    VFolderPermissionData,
    map_project_vfolder_to_project_admin_role,
    map_project_vfolder_to_project_user_role,
    map_user_vfolder_to_user_role,
    map_vfolder_permission_data_to_user_role,
)

# revision identifiers, used by Alembic.
revision = "4a60160ba8e0"
down_revision = "a4d56e86d9ee"
branch_labels = None
depends_on = None

mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()


class ScopeType(enum.StrEnum):
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"


class EntityType(enum.StrEnum):
    USER = "user"
    PROJECT = "project"
    DOMAIN = "domain"

    VFOLDER = "vfolder"
    IMAGE = "image"
    SESSION = "session"


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


class VFolderOwnershipType(enum.StrEnum):
    """
    Ownership type of virtual folder.
    """

    USER = "user"
    GROUP = "group"


class VFolderPermission(enum.StrEnum):
    # TODO: Replace this class with VFolderRBACPermission
    # Or rename this class to VFolderMountPermission
    """
    Permissions for a virtual folder given to a specific access key.
    RW_DELETE includes READ_WRITE and READ_WRITE includes READ_ONLY.
    """

    READ_ONLY = "ro"
    READ_WRITE = "rw"
    RW_DELETE = "wd"
    OWNER_PERM = "wd"  # resolved as RW_DELETE


class VFolderRow(Base):
    __tablename__ = "vfolders"
    __table_args__ = {"extend_existing": True}
    id = IDColumn("id")
    name = sa.Column(
        "name", sa.String(length=MODEL_VFOLDER_LENGTH_LIMIT), nullable=False, index=True
    )
    ownership_type = sa.Column(
        "ownership_type",
        EnumValueType(VFolderOwnershipType),
        default=VFolderOwnershipType.USER,
        nullable=False,
        index=True,
    )
    user = sa.Column("user", GUID, nullable=True)  # owner if user vfolder
    group = sa.Column("group", GUID, nullable=True)  # owner if project vfolder


class VFolderPermissionRow(Base):
    __tablename__ = "vfolder_permissions"
    __table_args__ = {"extend_existing": True}
    id = IDColumn()
    permission = sa.Column(
        "permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE
    )
    vfolder = sa.Column(
        "vfolder",
        GUID,
        sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user = sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=False)


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    uuid = IDColumn("uuid")
    role: UserRole = sa.Column("role", EnumValueType(UserRole), default=UserRole.USER)


class UserRoleRow(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"extend_existing": True}
    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)


class RoleRow(Base):
    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}
    id: uuid.UUID = IDColumn()
    name: str = sa.Column("name", sa.String(64), nullable=False)
    description: Optional[str] = sa.Column("description", sa.Text, nullable=True)


class ScopePermissionRow(Base):
    __tablename__ = "scope_permissions"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    entity_type: str = sa.Column(
        "entity_type", sa.String(32), nullable=False
    )  # e.g., "session", "vfolder", "image" etc.
    operation: str = sa.Column(
        "operation", sa.String(32), nullable=False
    )  # e.g., "create", "read", "delete", "grant:create", "grant:read" etc.
    scope_type: str = sa.Column(
        "scope_type", sa.String(32), nullable=False
    )  # e.g., "global", "domain", "project", "user" etc.
    scope_id: str = sa.Column(
        "scope_id", sa.String(64), nullable=False
    )  # e.g., "global", "domain_id", "project_id", "user_id" etc.


class AssociationScopesEntitiesRow(Base):
    __tablename__ = "association_scopes_entities"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = IDColumn()
    scope_type: str = sa.Column(
        "scope_type",
        sa.String(32),
        nullable=False,
    )  # e.g., "global", "domain", "project", "user" etc.
    scope_id: str = sa.Column(
        "scope_id",
        sa.String(64),
        nullable=False,
    )  # e.g., "global", "domain_id", "project_id", "user_id" etc.
    entity_type: str = sa.Column(
        "entity_type", sa.String(32), nullable=False
    )  # e.g., "session", "vfolder", "image" etc.
    entity_id: str = sa.Column(
        "entity_id",
        sa.String(64),
        nullable=False,
    )


def _insert_if_data_exists(db_conn: Connection, row_type, data: Collection) -> None:
    if data:
        db_conn.execute(sa.insert(row_type), data)


def _insert_from_create_input_group(
    db_conn: Connection, input_group: PermissionCreateInputGroup
) -> None:
    _insert_if_data_exists(db_conn, RoleRow, input_group.to_role_insert_data())
    _insert_if_data_exists(db_conn, UserRoleRow, input_group.to_user_role_insert_data())
    _insert_if_data_exists(
        db_conn, ScopePermissionRow, input_group.to_scope_permission_insert_data()
    )
    _insert_if_data_exists(
        db_conn,
        AssociationScopesEntitiesRow,
        input_group.to_association_scopes_entities_insert_data(),
    )


def _query_user_vfolder_row_with_user_role(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    """
    Query to get user vfolder rows with associated role ID.
    Assumes that all users have ONLY ONE role.
    """
    query = (
        sa.select(VFolderRow.id, VFolderRow.user, ScopePermissionRow.role_id)
        .select_from(
            sa.join(
                VFolderRow,
                ScopePermissionRow,
                VFolderRow.user == sa.cast(ScopePermissionRow.scope_id, UUID),
            )
        )
        .where(VFolderRow.user.is_not(sa.null()))
        .offset(offset)
        .limit(page_size)
        .order_by(VFolderRow.id)
    )
    return db_conn.execute(query).all()


def _migrate_user_vfolder_rows(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        rows = _query_user_vfolder_row_with_user_role(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = UserVFolderData(row.id, row.user)
            input_data = map_user_vfolder_to_user_role(row.role_id, data)
            input_group.merge(input_data)
        _insert_from_create_input_group(db_conn, input_group)


def _query_project_vfolder_with_project_role(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    """
    Query to get project vfolder rows with associated role ID.
    """
    query = (
        sa.select(
            VFolderRow.id,
            VFolderRow.group,
            ScopePermissionRow.role_id,
            RoleRow.name.label("role_name"),
        )
        .select_from(
            sa.join(
                VFolderRow,
                ScopePermissionRow,
                VFolderRow.group == sa.cast(ScopePermissionRow.scope_id, UUID),
            ).join(RoleRow, ScopePermissionRow.role_id == RoleRow.id)
        )
        .where(VFolderRow.group.is_not(sa.null()))
        .offset(offset)
        .limit(page_size)
        .order_by(VFolderRow.id)
    )
    return db_conn.execute(query).all()


def _migrate_project_vfolder_rows(db_conn: Connection) -> None:
    """
    Migrate project vfolder rows to RBAC table.
    Assumes that all projects have ONLY ONE admin role whose name ends with ADMIN_ROLE_NAME_SUFFIX.
    """
    offset = 0
    page_size = 1000

    while True:
        rows = _query_project_vfolder_with_project_role(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectVFolderData(row.id, row.group)
            if is_admin_role(row.role_name):
                input_data = map_project_vfolder_to_project_admin_role(row.role_id, data)
            else:
                input_data = map_project_vfolder_to_project_user_role(row.role_id, data)
            input_group.merge(input_data)
        _insert_from_create_input_group(db_conn, input_group)


def _query_vfolder_permission_with_user_role(
    db_conn: Connection, offset: int, page_size: int
) -> list[Row]:
    """
    Query to get vfolder permission rows with associated role ID.
    Assumes that all users have ONLY ONE role.
    """
    query = (
        sa.select(
            VFolderPermissionRow.vfolder, VFolderPermissionRow.user, ScopePermissionRow.role_id
        )
        .select_from(
            sa.join(
                VFolderPermissionRow,
                ScopePermissionRow,
                VFolderPermissionRow.user == sa.cast(ScopePermissionRow.scope_id, UUID),
            )
        )
        .offset(offset)
        .limit(page_size)
        .order_by(VFolderPermissionRow.id)
    )
    return db_conn.execute(query).all()


def _migrate_vfolder_permission_rows(db_conn: Connection) -> None:
    offset = 0
    page_size = 1000

    while True:
        rows = _query_vfolder_permission_with_user_role(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = VFolderPermissionData(row.vfolder, row.user)
            input_data = map_vfolder_permission_data_to_user_role(row.role_id, data)
            input_group.merge(input_data)
        _insert_from_create_input_group(db_conn, input_group)


def upgrade() -> None:
    conn = op.get_bind()
    _migrate_user_vfolder_rows(conn)
    _migrate_project_vfolder_rows(conn)
    _migrate_vfolder_permission_rows(conn)


def downgrade() -> None:
    pass
