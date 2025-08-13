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

from ai.backend.manager.data.permission.id import ScopeId
from ai.backend.manager.data.permission.scope_permission import (
    ScopePermissionData,
    ScopePermissionDataWithEntity,
)
from ai.backend.manager.data.permission.status import PermissionStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)

from ..base import (
    GUID,
    Base,
    IDColumn,
    StrEnumType,
)

if TYPE_CHECKING:
    from .association_scopes_entities import AssociationScopesEntitiesRow
    from .role import RoleRow


class ScopePermissionRow(Base):
    __tablename__ = "scope_permissions"
    __table_args__ = (
        sa.Index("ix_role_id_entity_type_scope_id", "status", "role_id", "entity_type", "scope_id"),
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
    entity_type: EntityType = sa.Column(
        "entity_type", StrEnumType(EntityType, length=32), nullable=False
    )
    operation: OperationType = sa.Column(
        "operation", StrEnumType(OperationType, length=32), nullable=False
    )
    scope_type: ScopeType = sa.Column(
        "scope_type", StrEnumType(ScopeType, length=32), nullable=False
    )
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

    @property
    def parsed_scope_id(self) -> ScopeId:
        return ScopeId(self.scope_type, self.scope_id)

    def to_data(self) -> ScopePermissionData:
        return ScopePermissionData(
            id=self.id,
            status=self.status,
            role_id=self.role_id,
            entity_type=self.entity_type,
            operation=self.operation,
            scope_id=self.parsed_scope_id,
            created_at=self.created_at,
        )

    def to_data_with_entity(self) -> ScopePermissionDataWithEntity:
        return ScopePermissionDataWithEntity(
            id=self.id,
            status=self.status,
            role_id=self.role_id,
            entity_type=self.entity_type,
            operation=self.operation,
            scope_id=self.parsed_scope_id,
            created_at=self.created_at,
            mapped_entities=[row.object_id() for row in self.mapped_entity_rows],
        )
