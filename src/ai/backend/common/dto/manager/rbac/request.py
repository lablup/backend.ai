"""
Request DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import AssignedUserOrderField, OrderDirection

__all__ = (
    "SearchUsersAssignedToRoleRequest",
    "StringFilter",
    "AssignedUserFilter",
    "AssignedUserOrder",
)


class AssignedUserFilter(BaseRequestModel):
    """Filter for assigned users."""

    username: Optional[StringFilter] = Field(default=None, description="Filter by username")
    email: Optional[StringFilter] = Field(default=None, description="Filter by email")


class AssignedUserOrder(BaseRequestModel):
    """Order specification for assigned users."""

    field: AssignedUserOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchUsersAssignedToRoleRequest(BaseRequestModel):
    """Request body for searching users assigned to a specific role."""

    filter: Optional[AssignedUserFilter] = Field(default=None, description="Filter conditions")
    order: Optional[AssignedUserOrder] = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
