"""
Request DTOs for Group (Project) v2 admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.group.types import GroupOrderField, OrderDirection

__all__ = (
    "CreateGroupInput",
    "DeleteGroupInput",
    "GroupFilter",
    "GroupOrder",
    "PurgeGroupInput",
    "SearchGroupsRequest",
    "UpdateGroupInput",
)


class CreateGroupInput(BaseRequestModel):
    """Input for creating a new group (project)."""

    name: str = Field(
        description="Group name. Must be unique within the domain.",
        max_length=64,
    )
    domain_name: str = Field(
        description="Name of the domain this group belongs to.",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the group.",
    )
    integration_id: str | None = Field(
        default=None,
        description="External system integration identifier for the group.",
    )
    resource_policy: str | None = Field(
        default=None,
        description="Name of the resource policy to apply to this group.",
    )


class UpdateGroupInput(BaseRequestModel):
    """Input for updating group information. All fields optional — only provided fields will be updated."""

    name: str | None = Field(
        default=None,
        description="New group name.",
        max_length=64,
    )
    description: str | Sentinel | None = Field(
        default=SENTINEL,
        description="New group description. Set to null to clear.",
    )
    is_active: bool | None = Field(
        default=None,
        description="Updated active status.",
    )
    integration_id: str | Sentinel | None = Field(
        default=SENTINEL,
        description="New external integration identifier. Set to null to clear.",
    )
    resource_policy: str | None = Field(
        default=None,
        description="Name of the updated resource policy to apply to this group.",
    )


class DeleteGroupInput(BaseRequestModel):
    """Input for soft-deleting a group."""

    group_id: UUID = Field(description="UUID of the group to soft-delete.")


class PurgeGroupInput(BaseRequestModel):
    """Input for permanently purging a group and all associated data."""

    group_id: UUID = Field(description="UUID of the group to permanently purge.")


class GroupFilter(BaseRequestModel):
    """Filter criteria for searching groups."""

    name: StringFilter | None = Field(default=None, description="Filter by group name.")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name.")
    is_active: bool | None = Field(default=None, description="Filter by active status.")


class GroupOrder(BaseRequestModel):
    """Order specification for group search results."""

    field: GroupOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="Order direction.",
    )


class SearchGroupsRequest(BaseRequestModel):
    """Request body for searching groups with filters, orders, and pagination."""

    filter: GroupFilter | None = Field(default=None, description="Filter conditions.")
    order: list[GroupOrder] | None = Field(default=None, description="Order specifications.")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Maximum items to return.",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip.")
