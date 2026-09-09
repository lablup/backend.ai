"""
Common types for RBAC DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import (
    OperationType,
    RoleSource,
    RoleStatus,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "EntityOrderField",
    "EntityType",
    "EntityTypeFilter",
    "EntityTypeScope",
    "OperationType",
    "OperationTypeDTO",
    "OperationTypeFilter",
    "OrderDirection",
    "PermissionOrderField",
    "PermissionSummary",
    "RoleAssignmentOrderField",
    "RoleOrderField",
    "RoleSource",
    "RoleSourceDTO",
    "RoleSourceFilter",
    "RoleStatus",
    "RoleStatusDTO",
    "RoleStatusFilter",
    "ScopeInputDTO",
    "UUIDScope",
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


class PermissionBitDTO(StrEnum):
    """One bit of the permission mask.

    Distinct from :class:`OperationTypeDTO`, which names an action: this names what is
    held. A cap is a set of these, and an empty set is no cap at all.
    """

    READ = "read"
    UPDATE = "update"
    CREATE = "create"
    SOFT_DELETE = "soft_delete"
    HARD_DELETE = "hard_delete"


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
    """Filter for a column holding an entity type."""

    equals: str | None = None
    in_: list[str] | None = None
    not_equals: str | None = None
    not_in: list[str] | None = None


class OperationTypeFilter(BaseRequestModel):
    """Filter for permission operation columns over ``OperationTypeDTO``."""

    equals: OperationTypeDTO | None = None
    in_: list[OperationTypeDTO] | None = None
    not_equals: OperationTypeDTO | None = None
    not_in: list[OperationTypeDTO] | None = None


class ScopeInputDTO(BaseRequestModel):
    """Scope reference for associating an entity with a scope."""

    scope_type: EntityType
    scope_id: str


class EntityTypeScope(BaseRequestModel):
    """A typed (entity type, id) pair naming one entity."""

    entity_type: EntityType
    entity_id: str


class UUIDScope(BaseRequestModel):
    """Single-UUID scope item wrapper.

    A thin wrapper around a UUID used as a scope item. The wrapper exists so
    that scope-input lists stay structurally uniform with other scope item
    types and leave room for per-item metadata in the future.
    """

    value: UUID


class PermissionSummary(BaseResponseModel):
    """Compact permission view for embedding inside RoleNode."""

    entity_type: EntityType
    operation: OperationType
