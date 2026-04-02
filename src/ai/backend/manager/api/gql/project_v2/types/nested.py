"""ProjectV2 GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

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
from ai.backend.manager.api.gql.common_types import VFolderHostPermissionEntryGQL
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_field,
    gql_pydantic_type,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin

from .enums import ProjectTypeEnum

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

    name: str = gql_field(description="Project name.")
    description: str | None = gql_field(description="Optional description of the project.")
    type: ProjectTypeEnum = gql_field(
        description="Project type determining its purpose. See ProjectTypeV2 enum."
    )
    integration_name: str | None = gql_field(description="External system integration identifier.")


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

    domain_name: str = gql_field(description="Name of the domain this project belongs to.")
    resource_policy: str = gql_field(
        description="Name of the project resource policy applied to this project."
    )


# ============================================================================
# Storage Configuration
# ============================================================================


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
class ProjectStorageInfoGQL(PydanticOutputMixin[ProjectStorageInfoDTO]):
    """Project storage configuration."""

    allowed_vfolder_hosts: list[VFolderHostPermissionEntryGQL] = gql_field(
        description="Storage hosts accessible to this project with their permissions. Each entry specifies a host and the operations allowed on it. Empty list means no storage access."
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

    is_active: bool | None = gql_field(
        description="Whether the project is active. Inactive projects cannot create new sessions or perform operations."
    )
    created_at: datetime | None = gql_field(description="Timestamp when the project was created.")
    modified_at: datetime | None = gql_field(
        description="Timestamp when the project was last modified."
    )
