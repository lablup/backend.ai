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
    from .resource_permission import ResourcePermissionRow
    from .role_permission import RolePermissionRow
    from .user_role import UserRoleRow


class RoleState(enum.StrEnum):
    ACTIVE = "active"
    # 'inactive' state is used when the role is temporarily disabled
    INACTIVE = "inactive"
    # 'deleted' state is used when the role is permanently removed
    DELETED = "deleted"


class RoleRow(Base):
    __tablename__ = "roles"

    id: uuid.UUID = IDColumn()
    name: str = sa.Column("name", sa.String(64), nullable=False)
    description: Optional[str] = sa.Column("description", sa.Text, nullable=True)
    state: str = sa.Column(
        "state",
        StrEnumType(RoleState),
        nullable=False,
        default=RoleState.ACTIVE,
        server_default=RoleState.ACTIVE,
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

    user_assignments: list[UserRoleRow] = relationship(
        "UserRoleRow",
        back_populates="assigned_role",
        primaryjoin="RoleRow.id == foreign(UserRoleRow.role_id)",
    )
    permission_rows: list[RolePermissionRow] = relationship(
        "RolePermissionRow",
        back_populates="role_row",
        primaryjoin="RoleRow.id == foreign(RolePermissionRow.role_id)",
    )
    resource_permission_rows: list[ResourcePermissionRow] = relationship(
        "ResourcePermissionRow",
        back_populates="role_row",
        primaryjoin="RoleRow.id == foreign(ResourcePermissionRow.role_id)",
    )
