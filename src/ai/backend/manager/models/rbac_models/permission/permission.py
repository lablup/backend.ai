from __future__ import annotations

import uuid
from typing import Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.permission import PermissionCreator, PermissionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.base import (
    GUID,
    Base,
    IntFlagType,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class PermissionRow(CreatedAtMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = (
        sa.Index("ix_permissions_role_scope", "role_id", "scope_type", "scope_id"),
        sa.Index(
            "ix_permissions_scope_entity",
            "scope_type",
            "scope_id",
            "entity_type",
            postgresql_include=["permission", "role_id"],
        ),
        sa.UniqueConstraint(
            "role_id",
            "scope_type",
            "scope_id",
            "entity_type",
            "permission",
            name="uq_permissions_role_scope_entity_permission",
        ),
        sa.CheckConstraint(
            "permission > 0 AND (permission & (permission - 1)) = 0",
            name="single_bit",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    role_id: Mapped[RoleID] = mapped_column(
        "role_id",
        GUID(RoleID),
        sa.ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope_type: Mapped[EntityType] = mapped_column(
        "scope_type", sa.String(length=32), nullable=False
    )
    scope_id: Mapped[str] = mapped_column("scope_id", sa.String(64), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", sa.String(length=32), nullable=False
    )
    # One row per operation bit; the bit is the row's identity.
    permission: Mapped[Permission] = mapped_column(
        "permission", IntFlagType(Permission), nullable=False
    )

    @classmethod
    def from_input(cls, input: PermissionCreator) -> Self:
        return cls(
            role_id=input.role_id,
            scope_type=input.scope_type,
            scope_id=input.scope_id,
            entity_type=input.entity_type,
            permission=single_bit(input.permission),
        )

    def to_data(self) -> PermissionData:
        return PermissionData(
            id=self.id,
            role_id=self.role_id,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            entity_type=self.entity_type,
            permission=self.permission,
            created_at=self.created_at,
        )
