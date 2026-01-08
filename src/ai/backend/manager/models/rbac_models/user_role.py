from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
)

import sqlalchemy as sa
from sqlalchemy.orm import (
    foreign,
    relationship,
)

from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IDColumn,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.user import UserRow

    from .role import RoleRow


def _get_role_row_join_condition():
    from .role import RoleRow

    return RoleRow.id == foreign(UserRoleRow.role_id)


def _get_user_row_join_condition():
    from ai.backend.manager.models.user import UserRow

    return UserRow.uuid == foreign(UserRoleRow.user_id)


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

    role_row: RoleRow | None = relationship(
        "RoleRow",
        back_populates="mapped_user_role_rows",
        primaryjoin=_get_role_row_join_condition,
    )
    user_row: UserRow | None = relationship(
        "UserRow",
        back_populates="role_assignments",
        primaryjoin=_get_user_row_join_condition,
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
