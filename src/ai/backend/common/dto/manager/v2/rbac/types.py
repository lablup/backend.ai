"""
Common types for RBAC DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import (
    Permission,
    RoleSource,
    RoleStatus,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "EntityType",
    "EntityTypeScope",
    "OrderDirection",
    "PermissionBitDTO",
    "PermissionBitFilter",
    "PermissionOrderField",
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

    @classmethod
    def of(cls, permission: Permission) -> PermissionBitDTO:
        """The name of a single permission bit."""
        for bit in cls:
            if permission is Permission[bit.name]:
                return bit
        raise ValueError(f"{permission!r} is not a single permission bit")

    def to_permission(self) -> Permission:
        """The bit this names, as a permission row records it."""
        return Permission[self.name]


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


class PermissionBitFilter(BaseRequestModel):
    """Filter for a permission-bit column over ``PermissionBitDTO``."""

    equals: PermissionBitDTO | None = None
    in_: list[PermissionBitDTO] | None = None
    not_equals: PermissionBitDTO | None = None
    not_in: list[PermissionBitDTO] | None = None


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
