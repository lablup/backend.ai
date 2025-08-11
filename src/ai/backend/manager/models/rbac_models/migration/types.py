import uuid
from dataclasses import dataclass, field
from typing import Any

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from .enums import EntityType, OperationType, RoleSource, RoleStatus, ScopeType

ROLE_NAME_PREFIX = "role_"
ADMIN_ROLE_NAME_SUFFIX = "_admin"


@dataclass
class UserRoleCreateInput:
    user_id: uuid.UUID
    role_id: uuid.UUID

    def to_dict(self) -> dict[str, uuid.UUID]:
        return {
            "user_id": self.user_id,
            "role_id": self.role_id,
        }


@dataclass
class ScopePermissionCreateInput:
    role_id: uuid.UUID
    entity_type: str
    operation: str
    scope_type: ScopeType
    scope_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "entity_type": self.entity_type,
            "operation": self.operation,
            "scope_type": self.scope_type.value,
            "scope_id": self.scope_id,
        }


@dataclass
class ObjectPermissionCreateInput:
    role_id: uuid.UUID
    entity_type: EntityType
    entity_id: str
    operation: OperationType

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "entity_type": self.entity_type.value,
            "entity_id": self.entity_id,
            "operation": self.operation.value,
        }


@dataclass
class AssociationScopesEntitiesCreateInput:
    scope_id: ScopeId
    object_id: ObjectId


@dataclass
class RoleCreateInput:
    name: str
    source: RoleSource
    status: RoleStatus = RoleStatus.ACTIVE

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "source": self.source.value,
            "status": self.status.value,
        }


@dataclass
class UserRoleCreateInputBeforeRoleCreation:
    user_id: uuid.UUID

    def to_input(self, role_id: uuid.UUID) -> UserRoleCreateInput:
        return UserRoleCreateInput(
            user_id=self.user_id,
            role_id=role_id,
        )


@dataclass
class ScopePermissionCreateInputBeforeRoleCreation:
    entity_type: str
    operation: str
    scope_type: ScopeType
    scope_id: str

    def to_input(self, role_id: uuid.UUID) -> ScopePermissionCreateInput:
        return ScopePermissionCreateInput(
            role_id=role_id,
            entity_type=self.entity_type,
            operation=self.operation,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
        )


@dataclass
class ObjectPermissionCreateInputBeforeRoleCreation:
    entity_type: EntityType
    entity_id: str
    operation: OperationType

    def to_input(self, role_id: uuid.UUID) -> ObjectPermissionCreateInput:
        return ObjectPermissionCreateInput(
            role_id=role_id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            operation=self.operation,
        )


@dataclass
class RoleCreationInputGroup:
    role: RoleCreateInput
    scope_permissions: list[ScopePermissionCreateInputBeforeRoleCreation] = field(
        default_factory=list
    )
    object_permissions: list[ObjectPermissionCreateInputBeforeRoleCreation] = field(
        default_factory=list
    )


@dataclass
class UserRoleMappingInputGroup:
    user_role_input: UserRoleCreateInput
    association_scopes_entities_input: AssociationScopesEntitiesCreateInput
