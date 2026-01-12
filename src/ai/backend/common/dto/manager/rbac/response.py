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
from ai.backend.common.data.permission.types import ScopeType

from .types import EntityType, OperationType, RoleSource, RoleStatus

__all__ = (
    "AssignRoleResponse",
    "AssignedUserDTO",
    "CreateObjectPermissionResponse",
    "CreatePermissionResponse",
    "CreateRoleResponse",
    "DeleteObjectPermissionResponse",
    "DeletePermissionResponse",
    "DeleteRoleResponse",
    "GetRoleResponse",
    "GetScopeTypesResponse",
    "ObjectPermissionDTO",
    "PaginationInfo",
    "PermissionDTO",
    "RevokeRoleResponse",
    "RoleDTO",
    "ScopeIDDTO",
    "SearchRolesResponse",
    "SearchScopeIDsResponse",
    "SearchUsersAssignedToRoleResponse",
    "UpdateRoleResponse",
)


class RoleDTO(BaseModel):
    """DTO for role data."""

    id: UUID = Field(description="Role ID")
    name: str = Field(description="Role name")
    source: RoleSource = Field(description="Role source")
    status: RoleStatus = Field(description="Role status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")
    description: Optional[str] = Field(default=None, description="Role description")


class AssignedUserDTO(BaseModel):
    """DTO for user assigned to a role."""

    user_id: UUID = Field(description="User ID")
    granted_by: Optional[UUID] = Field(default=None, description="ID of user who granted this role")
    granted_at: datetime = Field(description="Timestamp when the role was granted")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: Optional[int] = Field(default=None, description="Maximum items returned")


class CreateRoleResponse(BaseResponseModel):
    """Response for creating a role."""

    role: RoleDTO = Field(description="Created role")


class GetRoleResponse(BaseResponseModel):
    """Response for getting a role."""

    role: RoleDTO = Field(description="Role data")


class UpdateRoleResponse(BaseResponseModel):
    """Response for updating a role."""

    role: RoleDTO = Field(description="Updated role")


class DeleteRoleResponse(BaseResponseModel):
    """Response for deleting a role."""

    deleted: bool = Field(description="Whether the role was deleted")


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

    user_id: UUID = Field(description="User ID")
    role_id: UUID = Field(description="Role ID")


class SearchUsersAssignedToRoleResponse(BaseResponseModel):
    """Response for searching users assigned to a role."""

    users: list[AssignedUserDTO] = Field(description="List of assigned users")
    pagination: PaginationInfo = Field(description="Pagination information")


class PermissionDTO(BaseModel):
    """DTO for permission data."""

    id: UUID = Field(description="Permission ID")
    permission_group_id: UUID = Field(description="Permission group ID")
    entity_type: EntityType = Field(description="Entity type")
    operation: OperationType = Field(description="Operation type")


class ObjectPermissionDTO(BaseModel):
    """DTO for object permission data."""

    id: UUID = Field(description="Object permission ID")
    role_id: UUID = Field(description="Role ID")
    entity_type: EntityType = Field(description="Entity type")
    entity_id: str = Field(description="Entity ID")
    operation: OperationType = Field(description="Operation type")


class CreatePermissionResponse(BaseResponseModel):
    """Response for creating a permission."""

    permission: PermissionDTO = Field(description="Created permission")


class DeletePermissionResponse(BaseResponseModel):
    """Response for deleting a permission."""

    deleted: bool = Field(description="Whether the permission was deleted")


class CreateObjectPermissionResponse(BaseResponseModel):
    """Response for creating an object permission."""

    object_permission: ObjectPermissionDTO = Field(description="Created object permission")


class DeleteObjectPermissionResponse(BaseResponseModel):
    """Response for deleting an object permission."""

    deleted: bool = Field(description="Whether the object permission was deleted")


class GetScopeTypesResponse(BaseResponseModel):
    """Response for getting available scope types."""

    scope_types: list[ScopeType] = Field(description="List of available scope types")


class ScopeIDDTO(BaseModel):
    """DTO for scope ID data."""

    scope_type: ScopeType = Field(description="Scope type")
    id: str = Field(description="Scope ID (domain name, project UUID, or user UUID)")
    name: str = Field(description="Scope display name")


class SearchScopeIDsResponse(BaseResponseModel):
    """Response for searching scope IDs."""

    scope_ids: list[ScopeIDDTO] = Field(description="List of scope IDs")
    pagination: PaginationInfo = Field(description="Pagination information")
