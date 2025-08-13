from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    TYPE_CHECKING,
)

import sqlalchemy as sa
from sqlalchemy.orm import (
    relationship,
)

from ai.backend.manager.data.permission.id import ObjectId
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionData,
)
from ai.backend.manager.data.permission.status import PermissionStatus
from ai.backend.manager.data.permission.types import EntityType, OperationType

from ..base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    from .role import RoleRow


class ObjectPermissionRow(Base):
    __tablename__ = "object_permissions"
    __table_args__ = (sa.Index("ix_role_id_entity_id", "status", "role_id", "entity_id"),)

    id: uuid.UUID = IDColumn()
    status: PermissionStatus = sa.Column(
        "status",
        StrEnumType(PermissionStatus),
        nullable=False,
        default=PermissionStatus.ACTIVE,
        server_default=PermissionStatus.ACTIVE,
    )
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    entity_type: EntityType = sa.Column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    entity_id: str = sa.Column(
        "entity_id", sa.String(64), nullable=False
    )  # e.g., "session_id", "vfolder_id" etc.
    operation: OperationType = sa.Column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )
    created_at: datetime = sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    role_row: RoleRow = relationship(
        "RoleRow",
        back_populates="object_permission_rows",
        primaryjoin="RoleRow.id == foreign(ObjectPermissionRow.role_id)",
    )

    @property
    def parsed_object_id(self) -> ObjectId:
        return ObjectId(self.entity_type, self.entity_id)

    def to_data(self) -> ObjectPermissionData:
        return ObjectPermissionData(
            id=self.id,
            status=self.status,
            role_id=self.role_id,
            object_id=self.parsed_object_id,
            operation=self.operation,
            created_at=self.created_at,
        )
