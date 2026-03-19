"""
Response DTOs for RBAC DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import PermissionSummary, RoleSource, RoleStatus

__all__ = (
    "BulkAssignRoleResultPayload",
    "BulkRevokeRoleResultPayload",
    "BulkRoleOperationFailureInfo",
    "CreateRolePayload",
    "DeletePermissionPayload",
    "DeleteRolePayload",
    "PermissionNode",
    "PurgeRolePayload",
    "RoleAssignmentNode",
    "RoleNode",
    "UpdateRolePayload",
)


class RoleNode(BaseResponseModel):
    """Node model representing a role entity with optional nested permissions."""

    id: UUID = Field(description="Role ID")
    name: str = Field(description="Role name")
    description: str | None = Field(default=None, description="Role description")
    source: RoleSource = Field(description="Role source")
    status: RoleStatus = Field(description="Role status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    deleted_at: datetime | None = Field(default=None, description="Deletion timestamp")
    permissions: list[PermissionSummary] = Field(
        default_factory=list, description="Compact permission list"
    )


class CreateRolePayload(BaseResponseModel):
    """Payload for role creation mutation result."""

    role: RoleNode = Field(description="Created role")


class UpdateRolePayload(BaseResponseModel):
    """Payload for role update mutation result."""

    role: RoleNode = Field(description="Updated role")


class DeleteRolePayload(BaseResponseModel):
    """Payload for role soft-deletion mutation result."""

    id: UUID = Field(description="ID of the deleted role")


class PurgeRolePayload(BaseResponseModel):
    """Payload for role purge mutation result."""

    id: UUID = Field(description="ID of the purged role")


class DeletePermissionPayload(BaseResponseModel):
    """Payload for permission deletion mutation result."""

    id: UUID = Field(description="ID of the deleted permission")


class RoleAssignmentNode(BaseResponseModel):
    """Node representing a user-role assignment."""

    id: UUID = Field(description="Assignment ID")
    user_id: UUID = Field(description="Assigned user ID")
    role_id: UUID = Field(description="Assigned role ID")
    granted_by: UUID | None = Field(default=None, description="User who granted the assignment")
    granted_at: datetime = Field(description="Timestamp when the assignment was created")


class BulkRoleOperationFailureInfo(BaseResponseModel):
    """Failure detail for a single user in a bulk role operation."""

    user_id: UUID = Field(description="UUID of the user that failed")
    message: str = Field(description="Error message describing the failure")


class BulkAssignRoleResultPayload(BaseResponseModel):
    """Result payload for bulk role assignment."""

    successes: list[RoleAssignmentNode] = Field(
        default_factory=list, description="Successfully created role assignments"
    )
    failures: list[BulkRoleOperationFailureInfo] = Field(
        default_factory=list, description="Users that failed to be assigned"
    )


class BulkRevokeRoleResultPayload(BaseResponseModel):
    """Result payload for bulk role revocation."""

    successes: list[RoleAssignmentNode] = Field(
        default_factory=list, description="Successfully revoked role assignments"
    )
    failures: list[BulkRoleOperationFailureInfo] = Field(
        default_factory=list, description="Users that failed to be revoked"
    )


class PermissionNode(BaseResponseModel):
    """Node representing a scoped RBAC permission."""

    id: UUID = Field(description="Permission ID")
    role_id: UUID = Field(description="Role this permission belongs to")
    scope_type: str = Field(description="Scope element type value (e.g. 'domain', 'project')")
    scope_id: str = Field(description="Scope element ID")
    entity_type: str = Field(description="Entity element type value (e.g. 'session', 'vfolder')")
    operation: str = Field(description="Operation type value (e.g. 'read', 'create')")
