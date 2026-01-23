"""
Common types for RBAC system.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    PermissionStatus,
    RoleSource,
    RoleStatus,
)

__all__ = (
    "AssignedUserOrderField",
    "EntityType",
    "OperationType",
    "OrderDirection",
    "PermissionStatus",
    "RoleOrderField",
    "RoleSource",
    "RoleStatus",
    "ScopeOrderField",
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


class AssignedUserOrderField(StrEnum):
    """Fields available for ordering assigned users."""

    USERNAME = "username"
    EMAIL = "email"
    GRANTED_AT = "granted_at"


class ScopeOrderField(StrEnum):
    """Fields available for ordering scope IDs."""

    NAME = "name"
    CREATED_AT = "created_at"
