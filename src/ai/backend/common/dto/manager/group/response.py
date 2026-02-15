"""
Response DTOs for group/project management.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.deployment.response import PaginationInfo

__all__ = (
    # DTOs
    "GroupDTO",
    "GroupMemberDTO",
    # Responses
    "CreateGroupResponse",
    "GetGroupResponse",
    "SearchGroupsResponse",
    "UpdateGroupResponse",
    "DeleteGroupResponse",
    "AddGroupMembersResponse",
    "RemoveGroupMembersResponse",
    "ListGroupMembersResponse",
    # Pagination (re-exported)
    "PaginationInfo",
)


class GroupDTO(BaseModel):
    """DTO for group/project data."""

    id: UUID = Field(description="Group ID")
    name: str = Field(description="Group name")
    description: str | None = Field(default=None, description="Group description")
    is_active: bool = Field(description="Whether the group is active")
    created_at: datetime = Field(description="Creation timestamp")
    modified_at: datetime = Field(description="Last modification timestamp")
    domain_name: str = Field(description="Domain name the group belongs to")
    integration_id: str | None = Field(default=None, description="External integration ID")
    total_resource_slots: dict[str, Any] | None = Field(
        default=None, description="Total resource slot limits"
    )
    allowed_vfolder_hosts: dict[str, Any] | None = Field(
        default=None, description="Allowed vfolder host permissions"
    )
    resource_policy: str | None = Field(default=None, description="Resource policy name")
    container_registry: dict[str, Any] | None = Field(
        default=None, description="Container registry configuration"
    )


class GroupMemberDTO(BaseModel):
    """DTO for group membership data."""

    user_id: UUID = Field(description="User ID")
    group_id: UUID = Field(description="Group ID")


class CreateGroupResponse(BaseResponseModel):
    """Response for creating a group."""

    group: GroupDTO = Field(description="Created group")


class GetGroupResponse(BaseResponseModel):
    """Response for getting a group."""

    group: GroupDTO = Field(description="Group data")


class SearchGroupsResponse(BaseResponseModel):
    """Response for searching groups."""

    groups: list[GroupDTO] = Field(description="List of groups")
    pagination: PaginationInfo = Field(description="Pagination information")


class UpdateGroupResponse(BaseResponseModel):
    """Response for updating a group."""

    group: GroupDTO = Field(description="Updated group")


class DeleteGroupResponse(BaseResponseModel):
    """Response for deleting a group."""

    deleted: bool = Field(description="Whether the group was deleted")


class AddGroupMembersResponse(BaseResponseModel):
    """Response for adding members to a group."""

    members: list[GroupMemberDTO] = Field(description="Added members")


class RemoveGroupMembersResponse(BaseResponseModel):
    """Response for removing members from a group."""

    removed_count: int = Field(description="Number of members removed")


class ListGroupMembersResponse(BaseResponseModel):
    """Response for listing group members."""

    members: list[GroupMemberDTO] = Field(description="List of group members")
    pagination: PaginationInfo = Field(description="Pagination information")
