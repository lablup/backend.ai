"""
Common types for RBAC DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    RoleStatus,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "EntityOrderField",
    "EntityType",
    "EntityTypeFilter",
    "OperationType",
    "OperationTypeDTO",
    "OrderDirection",
    "PermissionOrderField",
    "PermissionSummary",
    "RBACElementTypeDTO",
    "RoleAssignmentOrderField",
    "RoleOrderField",
    "RoleSource",
    "RoleSourceDTO",
    "RoleSourceFilter",
    "RoleStatus",
    "RoleStatusDTO",
    "RoleStatusFilter",
    "ScopeInputDTO",
)


class RoleSourceDTO(StrEnum):
    """Role definition source enum for DTO layer."""

    SYSTEM = "system"
    CUSTOM = "custom"


class RoleStatusDTO(StrEnum):
    """Role status enum for DTO layer."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class OperationTypeDTO(StrEnum):
    """RBAC operation type enum for DTO layer."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    SOFT_DELETE = "soft-delete"
    HARD_DELETE = "hard-delete"
    GRANT_ALL = "grant:all"
    GRANT_READ = "grant:read"
    GRANT_UPDATE = "grant:update"
    GRANT_SOFT_DELETE = "grant:soft-delete"
    GRANT_HARD_DELETE = "grant:hard-delete"


class RBACElementTypeDTO(StrEnum):
    """Unified RBAC element type enum for DTO layer (matches GQL schema values)."""

    # Scope hierarchy
    DOMAIN = "domain"
    PROJECT = "project"
    USER = "user"

    # Root-query-enabled entities (scoped)
    SESSION = "session"
    VFOLDER = "vfolder"
    MODEL_DEPLOYMENT = "model_deployment"
    KEYPAIR = "keypair"
    NOTIFICATION_CHANNEL = "notification_channel"
    NETWORK = "network"
    RESOURCE_GROUP = "resource_group"
    CONTAINER_REGISTRY = "container_registry"
    STORAGE_HOST = "storage_host"
    AGENT = "agent"
    KERNEL = "kernel"
    ROUTING = "routing"
    IMAGE = "image"
    ARTIFACT = "artifact"
    ARTIFACT_REGISTRY = "artifact_registry"
    SESSION_TEMPLATE = "session_template"
    APP_CONFIG = "app_config"
    MODEL_CARD = "model_card"

    # Root-query-enabled entities (superadmin-only)
    RESOURCE_PRESET = "resource_preset"
    USER_RESOURCE_POLICY = "user_resource_policy"
    KEYPAIR_RESOURCE_POLICY = "keypair_resource_policy"
    PROJECT_RESOURCE_POLICY = "project_resource_policy"
    ROLE = "role"
    AUDIT_LOG = "audit_log"
    EVENT_LOG = "event_log"

    # Admin page access control
    PROJECT_ADMIN_PAGE = "project_admin_page"
    DOMAIN_ADMIN_PAGE = "domain_admin_page"

    # Auto-only entities used in permissions
    NOTIFICATION_RULE = "notification_rule"

    # Auto sub-entities with direct GET APIs
    DEPLOYMENT_TOKEN = "deployment:token"
    DEPLOYMENT_POLICY = "deployment:policy"
    DEPLOYMENT_REVISION = "deployment:revision"
    IMAGE_ALIAS = "image:alias"

    # Entity-level scopes
    ARTIFACT_REVISION = "artifact_revision"


class RoleOrderField(StrEnum):
    """Fields available for ordering roles."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RoleAssignmentOrderField(StrEnum):
    """Fields available for ordering role assignments."""

    USERNAME = "username"
    EMAIL = "email"
    GRANTED_AT = "granted_at"


class EntityOrderField(StrEnum):
    """Fields available for ordering entity associations."""

    ENTITY_TYPE = "entity_type"
    REGISTERED_AT = "registered_at"


class PermissionOrderField(StrEnum):
    """Fields available for ordering permissions."""

    ID = "id"
    ENTITY_TYPE = "entity_type"


class RoleSourceFilter(BaseRequestModel):
    """Filter for role source with equality and membership operators."""

    equals: str | None = None
    in_: list[str] | None = None
    not_equals: str | None = None
    not_in: list[str] | None = None


class RoleStatusFilter(BaseRequestModel):
    """Filter for role status with equality and membership operators."""

    equals: str | None = None
    in_: list[str] | None = None
    not_equals: str | None = None
    not_in: list[str] | None = None


class EntityTypeFilter(BaseRequestModel):
    """Filter for entity type with equality and membership operators."""

    equals: str | None = None
    in_: list[str] | None = None


class ScopeInputDTO(BaseRequestModel):
    """Scope reference for associating an entity with a scope."""

    scope_type: RBACElementTypeDTO
    scope_id: str


class PermissionSummary(BaseResponseModel):
    """Compact permission view for embedding inside RoleNode."""

    entity_type: EntityType
    operation: OperationType
