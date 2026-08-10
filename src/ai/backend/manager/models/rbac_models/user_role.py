from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
)


class UserRoleRow(Base):
    __tablename__ = "user_roles"
    __table_args__ = (sa.UniqueConstraint("user_id", "role_id", name="uq_user_id_role_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        "user_id",
        GUID,
        sa.ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        "role_id",
        GUID,
        sa.ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        "granted_by", GUID, nullable=True
    )  # Null if granted by system
    granted_at: Mapped[datetime] = mapped_column(
        "granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    def to_data(self) -> UserRoleAssignmentData:
        return UserRoleAssignmentData(
            id=self.id,
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
