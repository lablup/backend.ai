from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.data.permission.types import (
    ScopeType,
)

from ...base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)


class PermissionGroupRow(Base):
    __tablename__ = "permission_groups"
    __table_args__ = (sa.Index("ix_id_role_id_scope_id", "id", "role_id", "scope_id"),)

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    scope_type: ScopeType = sa.Column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
    scope_id: str = sa.Column(
        "scope_id", sa.String(64), nullable=False
    )  # e.g., "project_id", "user_id" etc.
