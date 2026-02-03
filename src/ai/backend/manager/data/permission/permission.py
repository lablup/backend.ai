from __future__ import annotations

import uuid
from dataclasses import dataclass

from .id import ScopeId
from .types import EntityType, OperationType, ScopeType


@dataclass
class PermissionCreator:
    permission_group_id: uuid.UUID
    entity_type: EntityType
    operation: OperationType


@dataclass
class PermissionData:
    id: uuid.UUID
    permission_group_id: uuid.UUID
    entity_type: EntityType
    operation: OperationType


@dataclass
class PermissionCreatorBeforePermissionGroupCreation:
    """
    Input for creating a permission before the permission group is created.
    Used when creating permissions as part of permission group creation.
    """

    entity_type: EntityType
    operation: OperationType


@dataclass
class ScopedPermissionCreateInput:
    """
    Input for creating a scoped permission using scope information.
    Used in update_role_permissions API to add permissions by scope.

    The system will automatically find or create the permission group
    based on (role_id, scope_type, scope_id) combination.
    """

    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    operation: OperationType

    def to_scope_id(self) -> ScopeId:
        """Convert to ScopeId for permission group lookup"""
        return ScopeId(scope_type=self.scope_type, scope_id=self.scope_id)
