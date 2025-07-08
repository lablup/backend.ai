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
)

if TYPE_CHECKING:
    from .role import RoleRow


class RolePermissionRow(Base):
    __tablename__ = "role_permissions"

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    entity_type: str = sa.Column(
        "entity_type", sa.String(32), nullable=False
    )  # e.g., "session", "vfolder", "image" etc.
    operation: str = sa.Column(
        "operation", sa.String(32), nullable=False
    )  # e.g., "create", "read", "delete", "grant:create", "grant:read" etc.
    scope_type: str = sa.Column(
        "scope_type", sa.String(32), nullable=False
    )  # e.g., "global", "domain", "project", "user" etc.
    scope_id: str = sa.Column(
        "scope_id", sa.String(64), nullable=False
    )  # e.g., "global", "domain_id", "project_id", "user_id" etc.
    created_at: datetime = sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )

    role_row: RoleRow = relationship(
        "RoleRow",
        back_populates="permission_rows",
        primaryjoin="RoleRow.id == foreign(RolePermissionRow.role_id)",
    )
