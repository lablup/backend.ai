"""
Response DTOs for Group (Project) v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo
from ai.backend.common.dto.manager.v2.group.types import ProjectType

__all__ = (
    "AdminSearchGroupsPayload",
    "DeleteProjectPayload",
    "ProjectBasicInfo",
    "ProjectLifecycleInfo",
    "ProjectNode",
    "ProjectOrganizationInfo",
    "ProjectPayload",
    "ProjectStorageInfo",
    "PurgeProjectPayload",
    "SearchProjectsPayload",
    "VFolderHostPermissionEntry",
)


class ProjectBasicInfo(BaseModel):
    """Basic project information."""

    name: str = Field(
        description="Project name.",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the project.",
    )
    type: ProjectType = Field(
        description="Project type determining its purpose. See ProjectType enum.",
    )
    integration_id: str | None = Field(
        default=None,
        description="External system integration identifier.",
    )


class ProjectOrganizationInfo(BaseModel):
    """Project's organizational context."""

    domain_name: str = Field(
        description="Name of the domain this project belongs to.",
    )
    resource_policy: str = Field(
        description="Name of the project resource policy applied to this project.",
    )


class VFolderHostPermissionEntry(BaseModel):
    """Storage host permission entry."""

    host: str = Field(
        description="Storage host identifier (e.g., 'default', 'storage-01').",
    )
    permissions: list[str] = Field(
        description=(
            "List of permissions granted for this host. "
            "See VFolderHostPermission enum for available permissions."
        ),
    )


class ProjectStorageInfo(BaseModel):
    """Project storage configuration."""

    allowed_vfolder_hosts: list[VFolderHostPermissionEntry] = Field(
        description=(
            "Storage hosts accessible to this project with their permissions. "
            "Each entry specifies a host and the operations allowed on it. "
            "Empty list means no storage access."
        ),
    )


class ProjectLifecycleInfo(BaseModel):
    """Project lifecycle information."""

    is_active: bool | None = Field(
        default=None,
        description=(
            "Whether the project is active. "
            "Inactive projects cannot create new sessions or perform operations."
        ),
    )
    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the project was created.",
    )
    modified_at: datetime | None = Field(
        default=None,
        description="Timestamp when the project was last modified.",
    )


class ProjectNode(BaseResponseModel):
    """Project entity with structured field groups."""

    id: UUID = Field(
        description="Unique identifier for the project (UUID).",
    )
    basic_info: ProjectBasicInfo = Field(
        description="Basic project information including name, type, and description.",
    )
    organization: ProjectOrganizationInfo = Field(
        description="Organizational context including domain membership and resource policy.",
    )
    storage: ProjectStorageInfo = Field(
        description="Storage configuration and vfolder host permissions.",
    )
    lifecycle: ProjectLifecycleInfo = Field(
        description="Lifecycle information including activation status and timestamps.",
    )


class ProjectPayload(BaseResponseModel):
    """Payload for single project mutation responses."""

    project: ProjectNode = Field(
        description="The project entity.",
    )


class SearchProjectsPayload(BaseResponseModel):
    """Payload for project search responses."""

    items: list[ProjectNode] = Field(
        description="List of project entities matching the search criteria.",
    )
    pagination: PaginationInfo = Field(
        description="Pagination information for the result set.",
    )


class DeleteProjectPayload(BaseResponseModel):
    """Payload for project deletion mutation."""

    deleted: bool = Field(
        description="Whether the deletion was successful.",
    )


class PurgeProjectPayload(BaseResponseModel):
    """Payload for project permanent deletion mutation."""

    purged: bool = Field(
        description="Whether the purge was successful.",
    )


class AdminSearchGroupsPayload(BaseResponseModel):
    """Payload for admin-scoped paginated group search results."""

    items: list[ProjectNode] = Field(description="List of group nodes.")
    total_count: int = Field(description="Total number of groups matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
