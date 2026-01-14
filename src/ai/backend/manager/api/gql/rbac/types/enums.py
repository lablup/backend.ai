"""GraphQL enum types for RBAC system."""

from __future__ import annotations

from enum import StrEnum

import strawberry

from ai.backend.manager.data.permission.types import (
    EntityType as EntityTypeInternal,
)
from ai.backend.manager.data.permission.types import (
    OperationType as OperationTypeInternal,
)
from ai.backend.manager.data.permission.types import (
    RoleSource as RoleSourceInternal,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as ScopeTypeInternal,
)


@strawberry.enum(name="EntityType", description="Entity types managed by the RBAC system")
class EntityTypeGQL(StrEnum):
    COMPUTE_SESSION = "compute_session"
    VFOLDER = "vfolder"
    IMAGE = "image"
    MODEL_SERVICE = "model_service"
    MODEL_ARTIFACT = "model_artifact"
    AGENT = "agent"
    RESOURCE_GROUP = "resource_group"
    STORAGE_HOST = "storage_host"
    APP_CONFIG = "app_config"
    NOTIFICATION = "notification"
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"
    ROLE = "role"
    ROLE_ASSIGNMENT = "role_assignment"

    @classmethod
    def from_internal(cls, internal_type: EntityTypeInternal) -> EntityTypeGQL:
        """Convert internal EntityType to GraphQL enum."""
        # Map internal "session" to GQL "compute_session"
        if internal_type == EntityTypeInternal.SESSION:
            return cls.COMPUTE_SESSION
        return cls(internal_type.value)

    def to_internal(self) -> EntityTypeInternal:
        """Convert GraphQL enum to internal EntityType."""
        # Map GQL "compute_session" to internal "session"
        if self == EntityTypeGQL.COMPUTE_SESSION:
            return EntityTypeInternal.SESSION
        return EntityTypeInternal(self.value)


@strawberry.enum(name="OperationType", description="Operations that can be performed on entities")
class OperationTypeGQL(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    SOFT_DELETE = "soft-delete"
    HARD_DELETE = "hard-delete"
    GRANT_ALL = "grant:all"  # Allow user to grant all permissions, including grant of grant
    GRANT_READ = "grant:read"
    GRANT_UPDATE = "grant:update"
    GRANT_SOFT_DELETE = "grant:soft-delete"
    GRANT_HARD_DELETE = "grant:hard-delete"

    @classmethod
    def from_internal(cls, internal_type: OperationTypeInternal) -> OperationTypeGQL:
        """Convert internal OperationType to GraphQL enum."""
        return cls(internal_type.value)

    def to_internal(self) -> OperationTypeInternal:
        """Convert GraphQL enum to internal OperationType."""
        return OperationTypeInternal(self.value)


@strawberry.enum(name="ScopeType", description="Scope types in the permission hierarchy")
class ScopeTypeGQL(StrEnum):
    GLOBAL = "global"
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"

    @classmethod
    def from_internal(cls, internal_type: ScopeTypeInternal) -> ScopeTypeGQL:
        """Convert internal ScopeType to GraphQL enum."""
        return cls(internal_type.value)

    def to_internal(self) -> ScopeTypeInternal:
        """Convert GraphQL enum to internal ScopeType."""
        return ScopeTypeInternal(self.value)


@strawberry.enum(name="RoleSource", description="Role source indicating how the role was created")
class RoleSourceGQL(StrEnum):
    SYSTEM = "system"
    CUSTOM = "custom"

    @classmethod
    def from_internal(cls, internal_type: RoleSourceInternal) -> RoleSourceGQL:
        """Convert internal RoleSource to GraphQL enum."""
        return cls(internal_type.value)

    def to_internal(self) -> RoleSourceInternal:
        """Convert GraphQL enum to internal RoleSource."""
        return RoleSourceInternal(self.value)


@strawberry.enum(name="RoleOrderField", description="Fields available for ordering role queries")
class RoleOrderField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


@strawberry.enum(
    name="ScopedPermissionOrderField",
    description="Fields available for ordering scoped permission queries",
)
class ScopedPermissionOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    OPERATION = "operation"
    SCOPE_TYPE = "scope_type"


@strawberry.enum(
    name="ObjectPermissionOrderField",
    description="Fields available for ordering object permission queries",
)
class ObjectPermissionOrderField(StrEnum):
    ENTITY_TYPE = "entity_type"
    ENTITY_ID = "entity_id"
    OPERATION = "operation"
