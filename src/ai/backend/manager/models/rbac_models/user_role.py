from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
)

import sqlalchemy as sa
from sqlalchemy.orm import (
    relationship,
)

from ..base import (
    GUID,
    Base,
    IDColumn,
)

if TYPE_CHECKING:
    from ..user import UserRow
    from .role import RoleRow


class UserRoleRow(Base):
    __tablename__ = "user_roles"

    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    granted_by: uuid.UUID = sa.Column(
        "granted_by", GUID, nullable=True
    )  # Null if granted by system
    granted_at: datetime = sa.Column(
        "granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    role_row: RoleRow = relationship(
        "RoleRow",
        back_populates="mapped_user_role_rows",
        primaryjoin="RoleRow.id == foreign(UserRoleRow.role_id)",
    )
    user_row: UserRow = relationship(
        "UserRow",
        back_populates="role_assignments",
        primaryjoin="UserRow.uuid == foreign(UserRoleRow.user_id)",
    )
