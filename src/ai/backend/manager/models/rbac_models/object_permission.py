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

from ..base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)
from .types import PermissionStatus

if TYPE_CHECKING:
    from .role import RoleRow


class ObjectPermissionRow(Base):
    __tablename__ = "object_permissions"
    __table_args__ = (
        sa.Index("ix_role_id_entity_id", "status", "role_id", "entity_id"),
        sa.UniqueConstraint(
            "entity_id", "operation", name="uq_object_permissions_entity_id_operation"
        ),
    )

    id: uuid.UUID = IDColumn()
    status: PermissionStatus = sa.Column(
        "status",
        StrEnumType(PermissionStatus),
        nullable=False,
        default=PermissionStatus.ACTIVE,
        server_default=PermissionStatus.ACTIVE,
    )
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    entity_type: str = sa.Column(
        "entity_type", sa.String(32), nullable=False
    )  # e.g., "session", "vfolder", "image" etc.
    entity_id: str = sa.Column(
        "entity_id", sa.String(64), nullable=False
    )  # e.g., "session_id", "vfolder_id" etc.
    operation: str = sa.Column(
        "operation", sa.String(32), nullable=False
    )  # e.g., "create", "read", "delete", "grant:create", "grant:read" etc.
    created_at: datetime = sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    role_row: RoleRow = relationship(
        "RoleRow",
        back_populates="object_permission_rows",
        primaryjoin="RoleRow.id == foreign(ObjectPermissionRow.role_id)",
    )
