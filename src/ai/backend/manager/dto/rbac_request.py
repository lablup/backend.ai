"""
Path parameter DTOs for RBAC API endpoints.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "GetRolePathParam",
    "UpdateRolePathParam",
    "DeleteRolePathParam",
    "SearchUsersAssignedToRolePathParam",
)


class GetRolePathParam(BaseRequestModel):
    """Path parameter for getting a role."""

    role_id: UUID = Field(description="The role ID to retrieve")


class UpdateRolePathParam(BaseRequestModel):
    """Path parameter for updating a role."""

    role_id: UUID = Field(description="The role ID to update")


class DeleteRolePathParam(BaseRequestModel):
    """Path parameter for deleting a role."""

    role_id: UUID = Field(description="The role ID to delete")


class SearchUsersAssignedToRolePathParam(BaseRequestModel):
    """Path parameter for searching users assigned to a role."""

    role_id: UUID = Field(description="The role ID to search assigned users for")
