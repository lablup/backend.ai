from __future__ import annotations

import uuid
from typing import Any, Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)


class ObjectPermissionRow(Base):
    """DEPRECATED: The ``object_permissions`` table is no longer used and scheduled for removal."""

    __tablename__ = "object_permissions"
    __table_args__ = (
        sa.Index("ix_id_role_id_entity_id", "id", "role_id", "entity_id"),
        sa.UniqueConstraint(
            "role_id",
            "entity_type",
            "entity_id",
            "operation",
            name="uq_object_permissions_role_entity_op",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    role_id: Mapped[RoleID] = mapped_column("role_id", GUID(RoleID), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    entity_id: Mapped[str] = mapped_column(
        "entity_id", sa.String(64), nullable=False
    )  # e.g., "project_id", "user_id" etc.
    operation: Mapped[OperationType] = mapped_column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )

    def object_id(self) -> ObjectId:
        return ObjectId(entity_type=self.entity_type, entity_id=self.entity_id)

    @classmethod
    def from_sa_row(cls, row: sa.engine.Row[Any]) -> Self:
        return cls(
            id=row.id,
            role_id=row.role_id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            operation=row.operation,
        )

    def to_data(self) -> ObjectPermissionData:
        return ObjectPermissionData(
            id=self.id,
            role_id=self.role_id,
            object_id=self.object_id(),
            operation=self.operation,
        )
