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
    USER = "user"
    PROJECT = "project"
    DOMAIN = "domain"
    VFOLDER = "vfolder"
    IMAGE = "image"
    COMPUTE_SESSION = "compute_session"
    ARTIFACT = "artifact"
    ARTIFACT_REGISTRY = "artifact_registry"
    APP_CONFIG = "app_config"
    NOTIFICATION_CHANNEL = "notification_channel"
    NOTIFICATION_RULE = "notification_rule"
    MODEL_DEPLOYMENT = "model_deployment"

    @classmethod
    def from_internal(cls, internal_type: EntityTypeInternal) -> EntityTypeGQL:
        """Convert internal EntityType to GraphQL enum."""
        match internal_type:
            case EntityTypeInternal.USER:
                return cls.USER
            case EntityTypeInternal.PROJECT:
                return cls.PROJECT
            case EntityTypeInternal.DOMAIN:
                return cls.DOMAIN
            case EntityTypeInternal.VFOLDER:
                return cls.VFOLDER
            case EntityTypeInternal.IMAGE:
                return cls.IMAGE
            case EntityTypeInternal.SESSION:
                return cls.COMPUTE_SESSION
            case EntityTypeInternal.ARTIFACT:
                return cls.ARTIFACT
            case EntityTypeInternal.ARTIFACT_REGISTRY:
                return cls.ARTIFACT_REGISTRY
            case EntityTypeInternal.APP_CONFIG:
                return cls.APP_CONFIG
            case EntityTypeInternal.NOTIFICATION_CHANNEL:
                return cls.NOTIFICATION_CHANNEL
            case EntityTypeInternal.NOTIFICATION_RULE:
                return cls.NOTIFICATION_RULE
            case EntityTypeInternal.MODEL_DEPLOYMENT:
                return cls.MODEL_DEPLOYMENT

    def to_internal(self) -> EntityTypeInternal:
        """Convert GraphQL enum to internal EntityType."""
        match self:
            case EntityTypeGQL.USER:
                return EntityTypeInternal.USER
            case EntityTypeGQL.PROJECT:
                return EntityTypeInternal.PROJECT
            case EntityTypeGQL.DOMAIN:
                return EntityTypeInternal.DOMAIN
            case EntityTypeGQL.VFOLDER:
                return EntityTypeInternal.VFOLDER
            case EntityTypeGQL.IMAGE:
                return EntityTypeInternal.IMAGE
            case EntityTypeGQL.COMPUTE_SESSION:
                return EntityTypeInternal.SESSION
            case EntityTypeGQL.ARTIFACT:
                return EntityTypeInternal.ARTIFACT
            case EntityTypeGQL.ARTIFACT_REGISTRY:
                return EntityTypeInternal.ARTIFACT_REGISTRY
            case EntityTypeGQL.APP_CONFIG:
                return EntityTypeInternal.APP_CONFIG
            case EntityTypeGQL.NOTIFICATION_CHANNEL:
                return EntityTypeInternal.NOTIFICATION_CHANNEL
            case EntityTypeGQL.NOTIFICATION_RULE:
                return EntityTypeInternal.NOTIFICATION_RULE
            case EntityTypeGQL.MODEL_DEPLOYMENT:
                return EntityTypeInternal.MODEL_DEPLOYMENT


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
