"""
Request DTOs for group/project management.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import GroupOrder

__all__ = (
    # Filters
    "GroupFilter",
    # Search/List requests
    "SearchGroupsRequest",
    # Create/Update requests
    "CreateGroupRequest",
    "UpdateGroupRequest",
    # Member management requests
    "AddGroupMembersRequest",
    "RemoveGroupMembersRequest",
    "ListGroupMembersRequest",
)


class GroupFilter(BaseRequestModel):
    """Filter for groups."""

    name: StringFilter | None = Field(default=None, description="Filter by group name")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    is_active: bool | None = Field(default=None, description="Filter by active status")


class SearchGroupsRequest(BaseRequestModel):
    """Request body for searching groups with filters, orders, and pagination."""

    filter: GroupFilter | None = Field(default=None, description="Filter conditions")
    order: GroupOrder | None = Field(default=None, description="Order specification")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class CreateGroupRequest(BaseRequestModel):
    """Request to create a new group/project."""

    name: str = Field(description="Group name")
    domain_name: str = Field(description="Domain name the group belongs to")
    description: str | None = Field(default=None, description="Group description")
    total_resource_slots: dict[str, Any] | None = Field(
        default=None, description="Total resource slot limits"
    )
    allowed_vfolder_hosts: dict[str, Any] | None = Field(
        default=None, description="Allowed vfolder host permissions"
    )
    integration_id: str | None = Field(default=None, description="External integration ID")
    resource_policy: str | None = Field(default=None, description="Resource policy name")


class UpdateGroupRequest(BaseRequestModel):
    """Request to update a group/project. All fields are optional."""

    name: str | None = Field(default=None, description="Updated group name")
    description: str | None = Field(default=None, description="Updated description")
    is_active: bool | None = Field(default=None, description="Updated active status")
    total_resource_slots: dict[str, Any] | None = Field(
        default=None, description="Updated total resource slot limits"
    )
    allowed_vfolder_hosts: dict[str, Any] | None = Field(
        default=None, description="Updated allowed vfolder host permissions"
    )
    integration_id: str | None = Field(default=None, description="Updated external integration ID")
    resource_policy: str | None = Field(default=None, description="Updated resource policy name")


class AddGroupMembersRequest(BaseRequestModel):
    """Request to add members to a group."""

    user_ids: list[UUID] = Field(description="List of user IDs to add")


class RemoveGroupMembersRequest(BaseRequestModel):
    """Request to remove members from a group."""

    user_ids: list[UUID] = Field(description="List of user IDs to remove")


class ListGroupMembersRequest(BaseRequestModel):
    """Request to list members of a group with pagination."""

    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
