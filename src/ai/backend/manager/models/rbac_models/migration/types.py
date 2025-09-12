import uuid
from dataclasses import dataclass
from typing import Any

from ai.backend.manager.data.permission.id import ObjectId, ScopeId

from .enums import RoleSource, RoleStatus, ScopeType

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
class AssociationScopesEntitiesCreateInput:
    scope_id: ScopeId
    object_id: ObjectId

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_type": self.scope_id.scope_type,
            "scope_id": self.scope_id.scope_id,
            "entity_type": self.object_id.entity_type,
            "entity_id": self.object_id.entity_id,
        }


@dataclass
class RoleCreateInput:
    name: str
    source: RoleSource
    status: RoleStatus = RoleStatus.ACTIVE

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "source": self.source,
            "status": self.status,
        }


@dataclass
class PermissionGroupCreateInput:
    role_id: uuid.UUID
    scope_type: ScopeType
    scope_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
        }


@dataclass
class PermissionCreateInput:
    permission_group_id: uuid.UUID
    entity_type: str
    operation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission_group_id": self.permission_group_id,
            "entity_type": self.entity_type,
            "operation": self.operation,
        }


@dataclass
class ObjectPermissionCreateInput:
    role_id: uuid.UUID
    entity_id: str
    entity_type: str
    operation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "operation": self.operation,
        }
