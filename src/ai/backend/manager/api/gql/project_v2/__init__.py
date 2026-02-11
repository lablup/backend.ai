"""ProjectV2 GraphQL API package.

Added in 26.2.0. Provides structured project management API with typed fields
replacing JSON scalars and organized into logical field groups.
"""

from .resolver import (
    admin_projects_v2,
    domain_projects_v2,
    project_domain_v2,
    project_v2,
)
from .types import (
    ProjectV2BasicInfoGQL,
    ProjectV2Connection,
    ProjectV2Edge,
    ProjectV2GQL,
    ProjectV2LifecycleInfoGQL,
    ProjectV2OrganizationInfoGQL,
    ProjectV2StorageInfoGQL,
    ProjectV2TypeEnum,
    VFolderHostPermissionEntryGQL,
    VFolderHostPermissionEnum,
)

__all__ = [
    # Queries
    "admin_projects_v2",
    "domain_projects_v2",
    "project_domain_v2",
    "project_v2",
    # Enums
    "ProjectV2TypeEnum",
    "VFolderHostPermissionEnum",
    # Nested types
    "ProjectV2BasicInfoGQL",
    "ProjectV2OrganizationInfoGQL",
    "VFolderHostPermissionEntryGQL",
    "ProjectV2StorageInfoGQL",
    "ProjectV2LifecycleInfoGQL",
    # Node types
    "ProjectV2GQL",
    "ProjectV2Edge",
    "ProjectV2Connection",
]
