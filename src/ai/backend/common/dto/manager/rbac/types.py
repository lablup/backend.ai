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
    "RoleStatus",
    "RoleSource",
    "EntityType",
    "OperationType",
    "PermissionStatus",
    "OrderDirection",
    "RoleOrderField",
    "AssignedUserOrderField",
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
