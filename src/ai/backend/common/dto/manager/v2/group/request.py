"""
Request DTOs for Group (Project) v2 admin REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.group.types import (
    OrderDirection,
    ProjectDomainFilter,
    ProjectOrderField,
    ProjectType,
    ProjectTypeFilter,
    ProjectUserFilter,
)

__all__ = (
    "AdminSearchProjectsInput",
    "AssignUsersToProjectInput",
    "CreateProjectInput",
    "DeleteProjectInput",
    "ProjectFilter",
    "ProjectOrder",
    "PurgeProjectInput",
    "SearchProjectsRequest",
    "UnassignUsersFromProjectInput",
    "UpdateProjectInput",
)


class CreateProjectInput(BaseRequestModel):
    """Input for creating a new project."""

    name: str = Field(
        description="Project name. Must be unique within the domain.",
        max_length=64,
    )
    domain_name: str = Field(
        description="Name of the domain this project belongs to.",
    )
    type: ProjectType | None = Field(
        default=None,
        description="Project type. Defaults to GENERAL if not specified.",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the project.",
    )
    integration_id: str | None = Field(
        default=None,
        description="External system integration identifier for the project.",
    )
    resource_policy: str | None = Field(
        default=None,
        description="Name of the resource policy to apply to this project.",
    )


class UpdateProjectInput(BaseRequestModel):
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


class DeleteProjectInput(BaseRequestModel):
    """Input for soft-deleting a group."""

    group_id: UUID = Field(description="UUID of the group to soft-delete.")


class PurgeProjectInput(BaseRequestModel):
    """Input for permanently purging a group and all associated data."""

    group_id: UUID = Field(description="UUID of the group to permanently purge.")


class ProjectFilter(BaseRequestModel):
    """Filter criteria for searching groups."""

    id: UUIDFilter | None = Field(default=None, description="Filter by project ID (UUID).")
    name: StringFilter | None = Field(default=None, description="Filter by group name.")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name.")
    type: ProjectTypeFilter | None = Field(default=None, description="Filter by project type.")
    is_active: bool | None = Field(default=None, description="Filter by active status.")
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by creation timestamp."
    )
    modified_at: DateTimeFilter | None = Field(
        default=None, description="Filter by last modification timestamp."
    )
    domain: ProjectDomainFilter | None = Field(
        default=None, description="Nested filter for domain conditions."
    )
    user: ProjectUserFilter | None = Field(
        default=None, description="Nested filter for user conditions."
    )
    AND: list[ProjectFilter] | None = Field(
        default=None, description="Combine filters with AND logic."
    )
    OR: list[ProjectFilter] | None = Field(
        default=None, description="Combine filters with OR logic."
    )
    NOT: list[ProjectFilter] | None = Field(
        default=None, description="Negate the specified filters."
    )


ProjectFilter.model_rebuild()


class ProjectOrder(BaseRequestModel):
    """Order specification for project search results."""

    field: ProjectOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="Order direction.",
    )


class SearchProjectsRequest(BaseRequestModel):
    """Request body for searching projects with filters, orders, and pagination."""

    filter: ProjectFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ProjectOrder] | None = Field(default=None, description="Order specifications.")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Maximum items to return.",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip.")


class AdminSearchProjectsInput(BaseRequestModel):
    """Input for admin search of projects with cursor and offset pagination."""

    filter: ProjectFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ProjectOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class AssignUsersToProjectInput(BaseRequestModel):
    """Input for assigning users to a project."""

    user_ids: list[UUID] = Field(description="List of user UUIDs to assign to the project.")


class UnassignUsersFromProjectInput(BaseRequestModel):
    """Input for unassigning users from a project."""

    user_ids: list[UUID] = Field(description="List of user UUIDs to unassign from the project.")
