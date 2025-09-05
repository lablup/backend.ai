from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional, Self

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.permission_group import (
    PermissionGroupCreator,
    PermissionGroupData,
)
from ai.backend.manager.data.permission.types import (
    ScopeType,
)

from ...base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    from ..role import RoleRow
    from .permission import PermissionRow


class PermissionGroupRow(Base):
    __tablename__ = "permission_groups"
    __table_args__ = (sa.Index("ix_id_role_id_scope_id", "id", "role_id", "scope_id"),)

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    scope_type: ScopeType = sa.Column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    scope_id: str = sa.Column(
        "scope_id", sa.String(64), nullable=False
    )  # e.g., "project_id", "user_id" etc.

    role_row: Optional[RoleRow] = relationship(
        "RoleRow",
        back_populates="permission_group_rows",
        primaryjoin="RoleRow.id == foreign(PermissionGroupRow.role_id)",
    )
    permission_rows: list[PermissionRow] = relationship(
        "PermissionRow",
        back_populates="permission_group_row",
        primaryjoin="PermissionGroupRow.id == foreign(PermissionRow.permission_group_id)",
    )

    def parsed_scope_id(self) -> ScopeId:
        return ScopeId(scope_type=self.scope_type, scope_id=self.scope_id)

    @classmethod
    def from_input(cls, input: PermissionGroupCreator) -> Self:
        return cls(
            role_id=input.role_id,
            scope_type=input.scope_id.scope_type,
            scope_id=input.scope_id.scope_id,
        )

    def to_data(self) -> PermissionGroupData:
        return PermissionGroupData(
            id=self.id,
            role_id=self.role_id,
            scope_id=ScopeId(scope_type=self.scope_type, scope_id=self.scope_id),
        )
