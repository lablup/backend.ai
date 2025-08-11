from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa

from ai.backend.manager.data.permission.scope_permission import (
    ScopePermissionData,
)
from ai.backend.manager.data.permission.status import PermissionStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
)

from ..base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)


class ScopePermissionRow(Base):
    __tablename__ = "scope_permissions"
    __table_args__ = (sa.Index("ix_status_permission_group_id", "status", "permission_group_id"),)

    id: uuid.UUID = IDColumn()
    status: PermissionStatus = sa.Column(
        "status",
        StrEnumType(PermissionStatus),
        nullable=False,
        default=PermissionStatus.ACTIVE,
        server_default=PermissionStatus.ACTIVE,
    )
    permission_group_id: uuid.UUID = sa.Column("permission_group_id", GUID, nullable=False)
    entity_type: EntityType = sa.Column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    operation: OperationType = sa.Column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )
    created_at: datetime = sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    def to_data(self) -> ScopePermissionData:
        return ScopePermissionData(
            id=self.id,
            status=self.status,
            entity_type=self.entity_type,
            operation=self.operation,
            created_at=self.created_at,
        )
