from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Optional,
    Self,
)

import sqlalchemy as sa
from sqlalchemy.orm import (
    relationship,
)

from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.role import (
    RoleCreateInput,
    RoleData,
)
from ai.backend.manager.data.permission.status import (
    RoleStatus,
)

from ..base import (
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    from .scope_permission import ScopePermissionRow
    from .user_role import UserRoleRow


class RoleRow(Base):
    __tablename__ = "roles"
    __table_args__ = (sa.Index("ix_id_status", "id", "status"),)

    id: uuid.UUID = IDColumn()
    name: str = sa.Column("name", sa.String(64), nullable=False)
    description: Optional[str] = sa.Column("description", sa.Text, nullable=True)
    status: RoleStatus = sa.Column(
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

    def to_data(self) -> RoleData:
        return RoleData(
            id=self.id,
            name=self.name,
            scope_id=ScopeId(
                scope_type=self.scope_type,
                scope_id=self.scope_id,
            ),
            operation=self.operation,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            description=self.description,
        )

    @classmethod
    def from_input(cls, data: RoleCreateInput) -> Self:
        return cls(
            name=data.name,
            operation=data.operation,
            scope_type=data.scope_id.scope_type,
            scope_id=data.scope_id.scope_id,
            status=data.status,
            description=data.description,
        )
