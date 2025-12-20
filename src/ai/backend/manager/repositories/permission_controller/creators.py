"""CreatorSpec implementations for permission-related entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.permission import (
    PermissionCreatorBeforePermissionGroupCreation,
)
from ai.backend.manager.data.permission.status import PermissionStatus, RoleStatus
from ai.backend.manager.data.permission.types import EntityType, OperationType, RoleSource
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class RoleCreatorSpec(CreatorSpec[RoleRow]):
    """CreatorSpec for role creation.

    Only defines the role itself. Permission groups and object permissions
    are passed separately to create_role() for better separation of concerns.
    """

    name: str
    source: RoleSource
    status: RoleStatus
    description: Optional[str] = None

    @override
    def build_row(self) -> RoleRow:
        return RoleRow(
            name=self.name,
            source=self.source,
            status=self.status,
            description=self.description,
        )


@dataclass
class PermissionGroupCreatorSpec(CreatorSpec[PermissionGroupRow]):
    """CreatorSpec for permission groups.

    Can include permissions to be created within the same transaction.
    """

    role_id: uuid.UUID
    scope_id: ScopeId
    permissions: list[PermissionCreatorBeforePermissionGroupCreation] = field(default_factory=list)

    @override
    def build_row(self) -> PermissionGroupRow:
        return PermissionGroupRow(
            role_id=self.role_id,
            scope_type=self.scope_id.scope_type,
            scope_id=self.scope_id.scope_id,
        )


@dataclass
class PermissionCreatorSpec(CreatorSpec[PermissionRow]):
    """CreatorSpec for permissions."""

    permission_group_id: uuid.UUID
    entity_type: EntityType
    operation: OperationType

    @override
    def build_row(self) -> PermissionRow:
        return PermissionRow(
            permission_group_id=self.permission_group_id,
            entity_type=self.entity_type,
            operation=self.operation,
        )


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
