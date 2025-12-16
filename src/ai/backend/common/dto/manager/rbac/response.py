"""
Response DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import RoleSource, RoleStatus

__all__ = (
    "RoleDTO",
    "AssignedUserDTO",
    "CreateRoleResponse",
    "UpdateRoleResponse",
    "DeleteRoleResponse",
    "GetRoleResponse",
    "SearchRolesResponse",
    "AssignRoleResponse",
    "RevokeRoleResponse",
    "SearchUsersAssignedToRoleResponse",
    "PaginationInfo",
)


class RoleDTO(BaseModel):
    """DTO for role data."""

    id: UUID = Field(description="Role ID")
    name: str = Field(description="Role name")
    source: RoleSource = Field(description="Role source")
    status: RoleStatus = Field(description="Role status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")
    description: Optional[str] = Field(default=None, description="Role description")


class AssignedUserDTO(BaseModel):
    """DTO for user assigned to a role."""

    user_id: UUID = Field(description="User ID")
    username: str = Field(description="Username")
    email: str = Field(description="User email")
    granted_by: Optional[UUID] = Field(default=None, description="ID of user who granted this role")
    granted_at: datetime = Field(description="Timestamp when the role was granted")


class CreateRoleResponse(BaseResponseModel):
    """Response for creating a role."""

    role: RoleDTO = Field(description="Created role")


class UpdateRoleResponse(BaseResponseModel):
    """Response for updating a role."""

    role: RoleDTO = Field(description="Updated role")


class DeleteRoleResponse(BaseResponseModel):
    """Response for deleting a role."""

    deleted: bool = Field(description="Whether the role was deleted")


class GetRoleResponse(BaseResponseModel):
    """Response for getting a role."""

    role: RoleDTO = Field(description="Role data")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: Optional[int] = Field(default=None, description="Maximum items returned")


class SearchRolesResponse(BaseResponseModel):
    """Response for searching roles."""

    roles: list[RoleDTO] = Field(description="List of roles")
    pagination: PaginationInfo = Field(description="Pagination information")


class AssignRoleResponse(BaseResponseModel):
    """Response for assigning a role to a user."""

    user_id: UUID = Field(description="User ID")
    role_id: UUID = Field(description="Role ID")
    granted_by: Optional[UUID] = Field(default=None, description="ID of user who granted the role")


class RevokeRoleResponse(BaseResponseModel):
    """Response for revoking a role from a user."""

    user_role_id: UUID = Field(description="ID of the revoked user-role association")
    user_id: UUID = Field(description="User ID")
    role_id: UUID = Field(description="Role ID")


class SearchUsersAssignedToRoleResponse(BaseResponseModel):
    """Response for searching users assigned to a role."""

    users: list[AssignedUserDTO] = Field(description="List of assigned users")
    pagination: PaginationInfo = Field(description="Pagination information")
