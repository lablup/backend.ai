"""
Path parameter DTOs for RBAC API endpoints.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.permission.types import EntityType, ScopeType

__all__ = (
    "DeleteObjectPermissionPathParam",
    "DeletePermissionPathParam",
    "GetRolePathParam",
    "SearchEntitiesPathParam",
    "SearchScopesPathParam",
    "SearchUsersAssignedToRolePathParam",
    "UpdateRolePathParam",
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


class SearchScopesPathParam(BaseRequestModel):
    """Path parameter for searching scopes."""

    scope_type: ScopeType = Field(
        description="Scope types", examples=["domain", "project", "user", "global"]
    )


class SearchEntitiesPathParam(BaseRequestModel):
    """Path parameter for searching entities within a scope."""

    scope_type: ScopeType = Field(
        description="Scope type", examples=["domain", "project", "user", "global"]
    )
    scope_id: str = Field(
        description="Scope ID (domain name, project UUID, or user UUID)",
        examples=["default", "550e8400-e29b-41d4-a716-446655440000"],
    )
    entity_type: EntityType = Field(
        description="Entity type to search",
        examples=["user", "vfolder", "session", "image"],
    )
