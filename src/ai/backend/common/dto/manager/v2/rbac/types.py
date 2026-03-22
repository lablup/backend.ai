"""
Common types for RBAC DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    RoleStatus,
)

__all__ = (
    "EntityType",
    "OperationType",
    "OrderDirection",
    "PermissionSummary",
    "RoleOrderField",
    "RoleSource",
    "RoleStatus",
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


class PermissionSummary(BaseResponseModel):
    """Compact permission view for embedding inside RoleNode."""

    entity_type: EntityType
    operation: OperationType
