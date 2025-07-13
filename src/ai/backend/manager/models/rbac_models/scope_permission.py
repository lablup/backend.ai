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
    from .association_scopes_entities import AssociationScopesEntitiesRow
    from .role import RoleRow


class ScopePermissionRow(Base):
    __tablename__ = "scope_permissions"
    __table_args__ = (
        sa.Index("ix_role_id_entity_type_scope_id", "status", "role_id", "entity_type", "scope_id"),
        sa.UniqueConstraint(
            "entity_type",
            "operation",
            "scope_id",
            name="uq_scope_permissions_entity_operation_scope_id",
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
        back_populates="scope_permission_rows",
        primaryjoin="RoleRow.id == foreign(ScopePermissionRow.role_id)",
    )
    mapped_entity_rows: list[AssociationScopesEntitiesRow] = relationship(
        "AssociationScopesEntitiesRow",
        back_populates="scope_permission_row",
        primaryjoin="ScopePermissionRow.scope_id == foreign(AssociationScopesEntitiesRow.scope_id)",
    )
