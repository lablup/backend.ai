from __future__ import annotations

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

from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
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
    __table_args__ = (sa.UniqueConstraint("user_id", "role_id", name="uq_user_id_role_id"),)

    id: uuid.UUID = IDColumn()
    user_id: uuid.UUID = sa.Column("user_id", GUID, nullable=False)
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    granted_by: uuid.UUID = sa.Column(
        "granted_by", GUID, nullable=True
    )  # Null if granted by system
    granted_at: datetime = sa.Column(
        "granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    role_row: Optional[RoleRow] = relationship(
        "RoleRow",
        back_populates="mapped_user_role_rows",
        primaryjoin="RoleRow.id == foreign(UserRoleRow.role_id)",
    )
    user_row: Optional[UserRow] = relationship(
        "UserRow",
        back_populates="role_assignments",
        primaryjoin="UserRow.uuid == foreign(UserRoleRow.user_id)",
    )

    def to_data(self) -> UserRoleAssignmentData:
        return UserRoleAssignmentData(
            user_id=self.user_id,
            role_id=self.role_id,
            granted_by=self.granted_by,
        )

    @classmethod
    def from_input(cls, input: UserRoleAssignmentInput) -> UserRoleRow:
        return cls(
            user_id=input.user_id,
            role_id=input.role_id,
            granted_by=input.granted_by,
        )
