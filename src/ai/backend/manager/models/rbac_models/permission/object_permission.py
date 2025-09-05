from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional, Self

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionCreateInput,
    ObjectPermissionData,
)
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
)

from ...base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    from ..role import RoleRow


class ObjectPermissionRow(Base):
    __tablename__ = "object_permissions"
    __table_args__ = (sa.Index("ix_id_role_id_entity_id", "id", "role_id", "entity_id"),)

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    entity_type: EntityType = sa.Column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    entity_id: str = sa.Column(
        "entity_id", sa.String(64), nullable=False
    )  # e.g., "project_id", "user_id" etc.
    operation: OperationType = sa.Column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )

    role_row: Optional[RoleRow] = relationship(
        "RoleRow",
        back_populates="object_permission_rows",
        primaryjoin="RoleRow.id == foreign(ObjectPermissionRow.role_id)",
    )

    def object_id(self) -> ObjectId:
        return ObjectId(entity_type=self.entity_type, entity_id=self.entity_id)

    @classmethod
    def from_input(cls, input: ObjectPermissionCreateInput) -> Self:
        return cls(
            role_id=input.role_id,
            entity_type=input.entity_type,
            entity_id=input.entity_id,
            operation=input.operation,
        )

    @classmethod
    def from_sa_row(cls, row: sa.engine.Row) -> Self:
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
