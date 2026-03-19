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

__all__ = (
    "EntityOrderField",
    "EntityType",
    "EntityTypeFilter",
    "OperationType",
    "OrderDirection",
    "PermissionOrderField",
    "PermissionSummary",
    "RoleAssignmentOrderField",
    "RoleOrderField",
    "RoleSource",
    "RoleSourceFilter",
    "RoleStatus",
    "RoleStatusFilter",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


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


class PermissionSummary(BaseResponseModel):
    """Compact permission view for embedding inside RoleNode."""

    entity_type: EntityType
    operation: OperationType
