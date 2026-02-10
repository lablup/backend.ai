"""
Request DTOs for RBAC system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    AssignedUserOrderField,
    EntityType,
    OperationType,
    OrderDirection,
    PermissionStatus,
    RoleOrderField,
    RoleSource,
    RoleStatus,
    ScopeOrderField,
)

__all__ = (
    "AssignRoleRequest",
    "AssignedUserFilter",
    "AssignedUserOrder",
    "CreateObjectPermissionRequest",
    "CreatePermissionRequest",
    "CreateRoleRequest",
    "RevokeRoleRequest",
    "RoleFilter",
    "RoleOrder",
    "ScopeFilter",
    "ScopeOrder",
    "SearchEntitiesRequest",
    "SearchRolesRequest",
    "SearchScopesRequest",
    "SearchUsersAssignedToRoleRequest",
    "StringFilter",
    "UpdateRoleRequest",
)


class CreateRoleRequest(BaseRequestModel):
    """Request to create a role."""

    name: str = Field(description="Role name")
    source: RoleSource = Field(default=RoleSource.CUSTOM, description="Role source")
    status: RoleStatus = Field(default=RoleStatus.ACTIVE, description="Role status")
    description: str | None = Field(default=None, description="Role description")


class UpdateRoleRequest(BaseRequestModel):
    """Request to update a role."""

    name: str | None = Field(default=None, description="Updated role name")
    source: RoleSource | None = Field(default=None, description="Updated role source")
    status: RoleStatus | None = Field(default=None, description="Updated role status")
    description: str | Sentinel | None = Field(
        default=SENTINEL, description="Updated role description"
    )


class DeleteRoleRequest(BaseRequestModel):
    """Request to delete a role."""

    role_id: UUID = Field(description="Role ID to delete")


class PurgeRoleRequest(BaseRequestModel):
    """Request to purge a role."""

    role_id: UUID = Field(description="Role ID to purge")


class AssignRoleRequest(BaseRequestModel):
    """Request to assign a role to a user."""

    user_id: UUID = Field(description="User ID to assign the role to")
    role_id: UUID = Field(description="Role ID to assign")
    granted_by: UUID | None = Field(
        default=None, description="User ID who granted this role assignment"
    )


class RevokeRoleRequest(BaseRequestModel):
    """Request to revoke a role from a user."""

    user_id: UUID = Field(description="User ID to revoke the role from")
    role_id: UUID = Field(description="Role ID to revoke")


class RoleFilter(BaseRequestModel):
    """Filter for roles."""

    name: StringFilter | None = Field(default=None, description="Filter by name")
    sources: list[RoleSource] | None = Field(default=None, description="Filter by role sources")
    statuses: list[RoleStatus] | None = Field(default=None, description="Filter by role statuses")


class RoleOrder(BaseRequestModel):
    """Order specification for roles."""

    field: RoleOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchRolesRequest(BaseRequestModel):
    """Request body for searching roles with filters, orders, and pagination."""

    filter: RoleFilter | None = Field(default=None, description="Filter conditions")
    order: list[RoleOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class AssignedUserFilter(BaseRequestModel):
    """Filter for assigned users."""

    username: StringFilter | None = Field(default=None, description="Filter by username")
    email: StringFilter | None = Field(default=None, description="Filter by email")
    granted_by: UUID | None = Field(default=None, description="Filter by 'granted_by' user ID")


class AssignedUserOrder(BaseRequestModel):
    """Order specification for assigned users."""

    field: AssignedUserOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchUsersAssignedToRoleRequest(BaseRequestModel):
    """Request body for searching users assigned to a specific role."""

    filter: AssignedUserFilter | None = Field(default=None, description="Filter conditions")
    order: list[AssignedUserOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class CreatePermissionRequest(BaseRequestModel):
    """Request to create a permission."""

    role_id: UUID = Field(description="Role ID for the permission")
    scope_type: ScopeType = Field(description="Scope type for the permission")
    scope_id: str = Field(description="Scope ID for the permission")
    entity_type: EntityType = Field(description="Entity type for the permission")
    operation: OperationType = Field(description="Operation type for the permission")


class CreateObjectPermissionRequest(BaseRequestModel):
    """Request to create an object permission for a role."""

    role_id: UUID = Field(description="Role ID to add the object permission to")
    entity_type: EntityType = Field(description="Entity type for the object permission")
    entity_id: str = Field(description="Entity ID (e.g., project_id, user_id)")
    operation: OperationType = Field(description="Operation type for the object permission")
    status: PermissionStatus = Field(
        default=PermissionStatus.ACTIVE, description="Permission status"
    )


class ScopeFilter(BaseRequestModel):
    """Filter for scopes."""

    name: StringFilter | None = Field(default=None, description="Filter by name")


class ScopeOrder(BaseRequestModel):
    """Order specification for scopes."""

    field: ScopeOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchScopesRequest(BaseRequestModel):
    """Request body for searching scopes with filters and pagination."""

    filter: ScopeFilter | None = Field(default=None, description="Filter conditions")
    order: list[ScopeOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchEntitiesRequest(BaseRequestModel):
    """Request body for searching entities within a scope."""

    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
