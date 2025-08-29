from __future__ import annotations

import uuid

import sqlalchemy as sa

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
