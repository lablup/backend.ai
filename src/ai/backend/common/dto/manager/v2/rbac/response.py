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
    "CreateRolePayload",
    "DeletePermissionPayload",
    "DeleteRolePayload",
    "PurgeRolePayload",
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
