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
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    from ..user import UserRow
    from .role import RoleRow


class UserRoleState(enum.StrEnum):
    ACTIVE = "active"
    # 'inactive' state is used when the role is temporarily disabled
    INACTIVE = "inactive"
    # 'expired' state is used when the role has reached its expiration date
    EXPIRED = "expired"
    # 'deleted' state is used when the role is permanently removed
    DELETED = "deleted"


class UserRoleRow(Base):
    __tablename__ = "user_roles"

    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    state = sa.Column(
        "state",
        StrEnumType(UserRoleState),
        nullable=False,
        default=UserRoleState.ACTIVE,
        server_default=UserRoleState.ACTIVE,
    )
    granted_by: uuid.UUID = sa.Column(
        "granted_by", GUID, nullable=True
    )  # Null if granted by system
    granted_at: datetime = sa.Column(
        "granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    expires_at: Optional[datetime] = sa.Column(
        "expires_at", sa.DateTime(timezone=True), nullable=True
    )
    deleted_at: Optional[datetime] = sa.Column(
        "deleted_at", sa.DateTime(timezone=True), nullable=True
    )

    assigned_role: RoleRow = relationship(
        "RoleRow",
        back_populates="user_assignments",
        primaryjoin="RoleRow.id == foreign(UserRoleRow.role_id)",
    )
    user_row: UserRow = relationship(
        "UserRow",
        back_populates="role_assignments",
        primaryjoin="UserRow.uuid == foreign(UserRoleRow.user_id)",
    )
