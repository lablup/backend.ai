"""GraphQL input types for RBAC system."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

import strawberry
from strawberry import ID

from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RoleSource as RoleSourceInternal
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.permission_controller.creators import RoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.updaters import RoleUpdaterSpec
from ai.backend.manager.types import OptionalState, TriState

from .enums import EntityTypeGQL, OperationTypeGQL, ScopeTypeGQL


@strawberry.input(description="Input for specifying a scope in mutations")
class ScopeInput:
    type: ScopeTypeGQL
    id: Optional[ID] = None


@strawberry.input(description="Input for creating a new custom role")
class CreateRoleInput:
    name: str
    description: Optional[str] = None
    scope: ScopeInput

    def to_creator(self) -> Creator[RoleRow]:
        """Convert to Creator for repository."""
        return Creator(
            spec=RoleCreatorSpec(
                name=self.name,
                source=RoleSourceInternal.CUSTOM,
                status=RoleStatus.ACTIVE,
                description=self.description,
            )
        )


@strawberry.input(description="Input for updating an existing role")
class UpdateRoleInput:
    id: ID
    name: Optional[str] = None
    description: Optional[str] = None

    def to_updater(self) -> Updater[RoleRow]:
        """Convert to Updater for repository."""
        return Updater(
            spec=RoleUpdaterSpec(
                name=OptionalState.update(self.name) if self.name else OptionalState.nop(),
                description=TriState.update(self.description)
                if self.description
                else TriState.nop(),
            ),
            pk_value=uuid.UUID(self.id),
        )


@strawberry.input(description="Input for scoped permissions")
class ScopedPermissionInput:
    scope_type: ScopeTypeGQL
    scope_id: ID
    entity_type: EntityTypeGQL
    operation: OperationTypeGQL


@strawberry.input(description="Input for object permissions")
class ObjectPermissionInput:
    entity_type: EntityTypeGQL
    entity_id: ID
    operation: OperationTypeGQL


@strawberry.input(description="Input for updating role permissions")
class UpdateRolePermissionsInput:
    role_id: ID
    scoped_permissions_to_add: Optional[list[ScopedPermissionInput]] = None
    object_permissions_to_add: Optional[list[ObjectPermissionInput]] = None
    scoped_permission_ids_to_delete: Optional[list[ID]] = None
    object_permission_ids_to_delete: Optional[list[ID]] = None


@strawberry.input(description="Input for creating a role assignment")
class CreateRoleAssignmentInput:
    user_id: ID
    role_id: ID
    scope: ScopeInput
    expires_at: Optional[datetime] = None
