from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa

from ai.backend.manager.data.permission.status import PermissionStatus
from ai.backend.manager.data.permission.types import (
    ScopeType,
)

from ..base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)


class PermissionGroupRow(Base):
    __tablename__ = "permission_groups"
    __table_args__ = (sa.Index("ix_id_status_role_id", "id", "status", "role_id"),)

    id: uuid.UUID = IDColumn()
    status: PermissionStatus = sa.Column(
        "status",
        StrEnumType(PermissionStatus),
        nullable=False,
        default=PermissionStatus.ACTIVE,
        server_default=PermissionStatus.ACTIVE,
    )
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    scope_type: ScopeType = sa.Column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    scope_id: str = sa.Column(
        "scope_id", sa.String(64), nullable=False
    )  # e.g., "project_id", "user_id" etc.
    created_at: datetime = sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
