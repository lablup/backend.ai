"""CreatorSpec implementations for permission-related entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.status import PermissionStatus
from ai.backend.manager.data.permission.types import EntityType, OperationType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ObjectPermissionCreatorSpec(CreatorSpec[ObjectPermissionRow]):
    """CreatorSpec for object permissions."""

    role_id: uuid.UUID
    entity_type: EntityType
    entity_id: str
    operation: OperationType
    status: PermissionStatus = PermissionStatus.ACTIVE

    @override
    def build_row(self) -> ObjectPermissionRow:
        return ObjectPermissionRow(
            role_id=self.role_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            operation=self.operation,
        )


@dataclass
class UserRoleCreatorSpec(CreatorSpec[UserRoleRow]):
    """CreatorSpec for user role mappings."""

    user_id: uuid.UUID
    role_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None

    @override
    def build_row(self) -> UserRoleRow:
        row = UserRoleRow(
            user_id=self.user_id,
            role_id=self.role_id,
        )
        if self.granted_by is not None:
            row.granted_by = self.granted_by
        return row


@dataclass
class AssociationScopesEntitiesCreatorSpec(CreatorSpec[AssociationScopesEntitiesRow]):
    """CreatorSpec for association between scopes and entities."""

    scope_id: ScopeId
    object_id: ObjectId

    @override
    def build_row(self) -> AssociationScopesEntitiesRow:
        return AssociationScopesEntitiesRow(
            scope_type=self.scope_id.scope_type,
            scope_id=self.scope_id.scope_id,
            entity_type=self.object_id.entity_type,
            entity_id=self.object_id.entity_id,
        )
