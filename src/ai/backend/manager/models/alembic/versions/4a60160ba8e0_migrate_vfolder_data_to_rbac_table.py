"""migrate vfolder data to rbac table

Revision ID: 4a60160ba8e0
Revises: 28fecac94e67
Create Date: 2025-07-30 14:44:14.346887

"""

import enum
import uuid
from typing import Any, Optional, cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection
from sqlalchemy.orm import registry, relationship

from ai.backend.common.defs import MODEL_VFOLDER_LENGTH_LIMIT
from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn, metadata
from ai.backend.manager.models.rbac_models.migrate.types import PermissionCreateInputGroup
from ai.backend.manager.models.rbac_models.migrate.vfolder import (
    vfolder_permission_row_to_rbac_row,
    vfolder_row_to_rbac_row,
)

# revision identifiers, used by Alembic.
revision = "4a60160ba8e0"
down_revision = "28fecac94e67"
branch_labels = None
depends_on = None

mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()  # TODO: remove Any after #422 is merged


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


class VFolderPermissionRow(Base):
    __tablename__ = "vfolder_permissions"
    __table_args__ = {"extend_existing": True}
    IDColumn()
    sa.Column("permission", EnumValueType(VFolderPermission), default=VFolderPermission.READ_WRITE)
    sa.Column(
        "vfolder",
        GUID,
        sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=False)

    vfolder_row = relationship("VFolderRow", back_populates="permission_rows")


class VFolderRow(Base):
    __tablename__ = "vfolders"
    __table_args__ = {"extend_existing": True}
    IDColumn("id")
    sa.Column("name", sa.String(length=MODEL_VFOLDER_LENGTH_LIMIT), nullable=False, index=True)
    sa.Column(
        "ownership_type",
        EnumValueType(VFolderOwnershipType),
        default=VFolderOwnershipType.USER,
        nullable=False,
        index=True,
    )
    sa.Column("user", GUID, nullable=True)  # owner if user vfolder
    sa.Column("group", GUID, nullable=True)  # owner if project vfolder


class RoleRow(Base):
    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}
    id: uuid.UUID = IDColumn()
    name: str = sa.Column("name", sa.String(64), nullable=False)
    description: Optional[str] = sa.Column("description", sa.Text, nullable=True)


class UserRoleRow(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"extend_existing": True}
    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)


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


def _migrate_vfolder_rows(conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        vfolder_query = (
            sa.select(VFolderRow).offset(offset).limit(page_size).order_by(VFolderRow.id)
        )
        vfolder_rows = conn.scalars(vfolder_query).all()
        vfolder_rows = cast(list[VFolderRow], vfolder_rows)
        offset += page_size
        if vfolder_rows is None or len(vfolder_rows) == 0:
            break
        input = PermissionCreateInputGroup()
        for vfolder_row in vfolder_rows:
            input_data = vfolder_row_to_rbac_row(vfolder_row)
            input.merge(input_data)
        conn.execute(sa.insert(RoleRow), input.to_role_insert_data())
        conn.execute(sa.insert(UserRoleRow), input.to_user_role_insert_data())
        conn.execute(sa.insert(ScopePermissionRow), input.to_scope_permission_insert_data())
        conn.execute(
            sa.insert(AssociationScopesEntitiesRow),
            input.to_association_scopes_entities_insert_data(),
        )


def _migrate_vfolder_permission_rows(conn: Connection) -> None:
    offset = 0
    page_size = 1000
    while True:
        vfolder_permission_query = (
            sa.select(VFolderPermissionRow)
            .offset(offset)
            .limit(page_size)
            .order_by(VFolderPermissionRow.id)
        )
        vfolder_permission_rows = conn.scalars(vfolder_permission_query).all()
        vfolder_permission_rows = cast(list[VFolderPermissionRow], vfolder_permission_rows)
        offset += page_size
        if vfolder_permission_rows is None or len(vfolder_permission_rows) == 0:
            break
        input = PermissionCreateInputGroup()
        for vfolder_permission_row in vfolder_permission_rows:
            input_data = vfolder_permission_row_to_rbac_row(vfolder_permission_row)
            input.merge(input_data)
        conn.execute(sa.insert(RoleRow), input.to_role_insert_data())
        conn.execute(sa.insert(UserRoleRow), input.to_user_role_insert_data())
        conn.execute(sa.insert(ScopePermissionRow), input.to_scope_permission_insert_data())
        conn.execute(
            sa.insert(AssociationScopesEntitiesRow),
            input.to_association_scopes_entities_insert_data(),
        )


def upgrade() -> None:
    conn = op.get_bind()
    _migrate_vfolder_rows(conn)
    _migrate_vfolder_permission_rows(conn)


def downgrade() -> None:
    pass
