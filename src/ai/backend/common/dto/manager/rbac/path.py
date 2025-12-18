"""
Path parameter DTOs for RBAC API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "GetRolePathParam",
    "UpdateRolePathParam",
    "SearchUsersAssignedToRolePathParam",
    "DeletePermissionPathParam",
    "DeleteObjectPermissionPathParam",
)


class GetRolePathParam(BaseRequestModel):
    """Path parameter for getting a role."""

    role_id: UUID = Field(description="The role ID to retrieve")


class UpdateRolePathParam(BaseRequestModel):
    """Path parameter for updating a role."""

    role_id: UUID = Field(description="The role ID to update")


class SearchUsersAssignedToRolePathParam(BaseRequestModel):
    """Path parameter for searching users assigned to a role."""

    role_id: UUID = Field(description="The role ID to search assigned users for")


class DeletePermissionPathParam(BaseRequestModel):
    """Path parameter for deleting a permission."""

    permission_id: UUID = Field(description="The permission ID to delete")


class DeleteObjectPermissionPathParam(BaseRequestModel):
    """Path parameter for deleting an object permission."""

    object_permission_id: UUID = Field(description="The object permission ID to delete")
