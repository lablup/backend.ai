"""ProjectV2 GraphQL nested types for structured field groups."""

from __future__ import annotations

from datetime import datetime

import strawberry

from .enums import ProjectV2TypeEnum, VFolderHostPermissionEnum

# ============================================================================
# Basic Information
# ============================================================================


@strawberry.type(
    name="ProjectV2BasicInfo",
    description=(
        "Added in 26.2.0. Basic project information. "
        "Contains identity and descriptive fields for the project."
    ),
)
class ProjectV2BasicInfoGQL:
    """Basic project information."""

    name: str = strawberry.field(description="Project name.")
    description: str | None = strawberry.field(description="Optional description of the project.")
    type: ProjectV2TypeEnum = strawberry.field(
        description="Project type determining its purpose. See ProjectTypeV2 enum."
    )
    integration_id: str | None = strawberry.field(
        description="External system integration identifier."
    )


# ============================================================================
# Organization Context
# ============================================================================


@strawberry.type(
    name="ProjectV2OrganizationInfo",
    description=(
        "Added in 26.2.0. Project's organizational context. "
        "Contains domain membership and resource policy information."
    ),
)
class ProjectV2OrganizationInfoGQL:
    """Project's organizational context."""

    domain_name: str = strawberry.field(description="Name of the domain this project belongs to.")
    resource_policy: str = strawberry.field(
        description="Name of the project resource policy applied to this project."
    )


# ============================================================================
# Storage Configuration
# ============================================================================


@strawberry.type(
    name="VFolderHostPermissionEntry",
    description=(
        "Added in 26.2.0. Storage host permission configuration. "
        "Defines what operations are allowed for a specific storage host."
    ),
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


@strawberry.type(
    name="ProjectV2StorageInfo",
    description=(
        "Added in 26.2.0. Project storage configuration. "
        "Contains allowed virtual folder hosts and their permissions."
    ),
)
class ProjectV2StorageInfoGQL:
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


@strawberry.type(
    name="ProjectV2LifecycleInfo",
    description=(
        "Added in 26.2.0. Project lifecycle information. "
        "Contains activation status and timestamp tracking."
    ),
)
class ProjectV2LifecycleInfoGQL:
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
