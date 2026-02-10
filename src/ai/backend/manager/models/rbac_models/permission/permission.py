from __future__ import annotations

import uuid
from typing import Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.permission import PermissionCreator, PermissionData
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)


class PermissionRow(Base):  # type: ignore[misc]
    __tablename__ = "permissions"
    __table_args__ = (
        sa.Index("ix_id_permission_group_id", "id", "permission_group_id"),
        sa.Index("ix_permissions_role_scope", "role_id", "scope_type", "scope_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    permission_group_id: Mapped[uuid.UUID] = mapped_column(
        "permission_group_id",
        GUID,
        sa.ForeignKey("permission_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        "role_id",
        GUID,
        nullable=False,
    )
    scope_type: Mapped[ScopeType] = mapped_column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    scope_id: Mapped[str] = mapped_column("scope_id", sa.String(64), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    operation: Mapped[OperationType] = mapped_column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )

    @classmethod
    def from_input(cls, input: PermissionCreator) -> Self:
        return cls(
            permission_group_id=input.permission_group_id,
            role_id=input.role_id,
            scope_type=input.scope_type,
            scope_id=input.scope_id,
            entity_type=input.entity_type,
            operation=input.operation,
        )

    def to_data(self) -> PermissionData:
        return PermissionData(
            id=self.id,
            permission_group_id=self.permission_group_id,
            role_id=self.role_id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            entity_type=self.entity_type,
            operation=self.operation,
        )
