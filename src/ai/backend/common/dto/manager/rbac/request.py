"""
Request DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    AssignedUserOrderField,
    OrderDirection,
    RoleOrderField,
    RoleSource,
    RoleStatus,
)

__all__ = (
    "CreateRoleRequest",
    "UpdateRoleRequest",
    "SearchRolesRequest",
    "AssignRoleRequest",
    "RevokeRoleRequest",
    "SearchUsersAssignedToRoleRequest",
    "StringFilter",
    "RoleFilter",
    "RoleOrder",
    "AssignedUserFilter",
    "AssignedUserOrder",
)


class CreateRoleRequest(BaseRequestModel):
    """Request to create a role."""

    name: str = Field(description="Role name")
    source: RoleSource = Field(default=RoleSource.CUSTOM, description="Role source")
    status: RoleStatus = Field(default=RoleStatus.ACTIVE, description="Role status")
    description: Optional[str] = Field(default=None, description="Role description")


class UpdateRoleRequest(BaseRequestModel):
    """Request to update a role."""

    name: Optional[str] = Field(default=None, description="Updated role name")
    source: Optional[RoleSource] = Field(default=None, description="Updated role source")
    status: Optional[RoleStatus] = Field(default=None, description="Updated role status")
    description: Optional[str | Sentinel] = Field(
        default=SENTINEL, description="Updated role description"
    )


class AssignRoleRequest(BaseRequestModel):
    """Request to assign a role to a user."""

    user_id: UUID = Field(description="User ID to assign the role to")
    role_id: UUID = Field(description="Role ID to assign")
    granted_by: Optional[UUID] = Field(
        default=None, description="User ID who granted this role assignment"
    )


class RevokeRoleRequest(BaseRequestModel):
    """Request to revoke a role from a user."""

    user_id: UUID = Field(description="User ID to revoke the role from")
    role_id: UUID = Field(description="Role ID to revoke")


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
