"""ProjectV2 GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

import strawberry

from ai.backend.common.dto.manager.v2.group.response import (
    ProjectBasicInfo as ProjectBasicInfoDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    ProjectLifecycleInfo as ProjectLifecycleInfoDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    ProjectOrganizationInfo as ProjectOrganizationInfoDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    ProjectStorageInfo as ProjectStorageInfoDTO,
)
from ai.backend.common.dto.manager.v2.group.response import (
    VFolderHostPermissionEntry as VFolderHostPermissionEntryDTO,
)
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_pydantic_type

from .enums import ProjectTypeEnum, VFolderHostPermissionEnum

# ============================================================================
# Basic Information
# ============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Basic project information. Contains identity and descriptive fields for the project."
        ),
    ),
    model=ProjectBasicInfoDTO,
    name="ProjectBasicInfo",
)
class ProjectBasicInfoGQL:
    """Basic project information."""

    name: str = strawberry.field(description="Project name.")
    description: str | None = strawberry.field(description="Optional description of the project.")
    type: ProjectTypeEnum = strawberry.field(
        description="Project type determining its purpose. See ProjectTypeV2 enum."
    )
    integration_id: str | None = strawberry.field(
        description="External system integration identifier."
    )


# ============================================================================
# Organization Context
# ============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Project's organizational context. "
            "Contains domain membership and resource policy information."
        ),
    ),
    model=ProjectOrganizationInfoDTO,
    name="ProjectOrganizationInfo",
)
class ProjectOrganizationInfoGQL:
    """Project's organizational context."""

    domain_name: str = strawberry.field(description="Name of the domain this project belongs to.")
    resource_policy: str = strawberry.field(
        description="Name of the project resource policy applied to this project."
    )


# ============================================================================
# Storage Configuration
# ============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Storage host permission configuration. "
            "Defines what operations are allowed for a specific storage host."
        ),
    ),
    model=VFolderHostPermissionEntryDTO,
    name="VFolderHostPermissionEntry",
)
class VFolderHostPermissionEntryGQL:
    """Storage host permission entry."""

    host: str = strawberry.field(
        description="Storage host identifier (e.g., 'default', 'storage-01')."
    )
    permissions: list[VFolderHostPermissionEnum] = strawberry.field(
        description=(
            "List of permissions granted for this host. "
            "See VFolderHostPermissionV2 enum for available permissions."
        )
    )


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Project storage configuration. "
            "Contains allowed virtual folder hosts and their permissions."
        ),
    ),
    model=ProjectStorageInfoDTO,
    name="ProjectStorageInfo",
)
class ProjectStorageInfoGQL:
    """Project storage configuration."""

    allowed_vfolder_hosts: list[VFolderHostPermissionEntryGQL] = strawberry.field(
        description=(
            "Storage hosts accessible to this project with their permissions. "
            "Each entry specifies a host and the operations allowed on it. "
            "Empty list means no storage access."
        )
    )


# ============================================================================
# Lifecycle Information
# ============================================================================


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Project lifecycle information. Contains activation status and timestamp tracking."
        ),
    ),
    model=ProjectLifecycleInfoDTO,
    name="ProjectLifecycleInfo",
)
class ProjectLifecycleInfoGQL:
    """Project lifecycle information."""

    is_active: bool | None = strawberry.field(
        description=(
            "Whether the project is active. "
            "Inactive projects cannot create new sessions or perform operations."
        )
    )
    created_at: datetime | None = strawberry.field(
        description="Timestamp when the project was created."
    )
    modified_at: datetime | None = strawberry.field(
        description="Timestamp when the project was last modified."
    )
