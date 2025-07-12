from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Optional,
)

import sqlalchemy as sa
from sqlalchemy.orm import (
    relationship,
)

from ..base import (
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    from .object_permission import ObjectPermissionRow
    from .scope_permission import ScopePermissionRow
    from .user_role import UserRoleRow


class RoleStatus(enum.StrEnum):
    ACTIVE = "active"
    # 'inactive' status is used when the role is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' status is used when the role is permanently removed
    DELETED = "deleted"


class RoleRow(Base):
    __tablename__ = "roles"

    id: uuid.UUID = IDColumn()
    name: str = sa.Column("name", sa.String(64), nullable=False)
    description: Optional[str] = sa.Column("description", sa.Text, nullable=True)
    status: str = sa.Column(
        "status",
        StrEnumType(RoleStatus),
        nullable=False,
        default=RoleStatus.ACTIVE,
        server_default=RoleStatus.ACTIVE,
    )
    created_at: datetime = sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Optional[datetime] = sa.Column(
        "updated_at", sa.DateTime(timezone=True), nullable=True
    )
    deleted_at: Optional[datetime] = sa.Column(
        "deleted_at", sa.DateTime(timezone=True), nullable=True
    )

    mapped_user_role_rows: list[UserRoleRow] = relationship(
        "UserRoleRow",
        back_populates="role_row",
        primaryjoin="RoleRow.id == foreign(UserRoleRow.role_id)",
    )
    scope_permission_rows: list[ScopePermissionRow] = relationship(
        "ScopePermissionRow",
        back_populates="role_row",
        primaryjoin="RoleRow.id == foreign(ScopePermissionRow.role_id)",
    )
    object_permission_rows: list[ObjectPermissionRow] = relationship(
        "ObjectPermissionRow",
        back_populates="role_row",
        primaryjoin="RoleRow.id == foreign(ObjectPermissionRow.role_id)",
    )
