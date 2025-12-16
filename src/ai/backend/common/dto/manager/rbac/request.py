"""
Request DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    OrderDirection,
    RoleOrderField,
    RoleSource,
    RoleStatus,
)

__all__ = (
    "SearchRolesRequest",
    "StringFilter",
    "RoleFilter",
    "RoleOrder",
)


class RoleFilter(BaseRequestModel):
    """Filter for roles."""

    name: Optional[StringFilter] = Field(default=None, description="Filter by name")
    sources: Optional[list[RoleSource]] = Field(default=None, description="Filter by role sources")
    statuses: Optional[list[RoleStatus]] = Field(
        default=None, description="Filter by role statuses"
    )


class RoleOrder(BaseRequestModel):
    """Order specification for roles."""

    field: RoleOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchRolesRequest(BaseRequestModel):
    """Request body for searching roles with filters, orders, and pagination."""

    filter: Optional[RoleFilter] = Field(default=None, description="Filter conditions")
    order: Optional[RoleOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
