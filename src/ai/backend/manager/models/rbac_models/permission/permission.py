from __future__ import annotations

import uuid
from typing import Self

import sqlalchemy as sa

from ai.backend.manager.data.permission.permission import PermissionCreator, PermissionData
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


class PermissionRow(Base):
    __tablename__ = "permissions"
    __table_args__ = (sa.Index("ix_id_permission_group_id", "id", "permission_group_id"),)

    id: uuid.UUID = IDColumn()
    permission_group_id: uuid.UUID = sa.Column("permission_group_id", GUID, nullable=False)
    entity_type: EntityType = sa.Column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    operation: OperationType = sa.Column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )

    @classmethod
    def from_input(cls, input: PermissionCreator) -> Self:
        return cls(
            permission_group_id=input.permission_group_id,
            entity_type=input.entity_type,
            operation=input.operation,
        )

    def to_data(self) -> PermissionData:
        return PermissionData(
            id=self.id,
            permission_group_id=self.permission_group_id,
            entity_type=self.entity_type,
            operation=self.operation,
        )
