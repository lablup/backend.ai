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
    ProjectBasicInfoGQL,
    ProjectLifecycleInfoGQL,
    ProjectOrganizationInfoGQL,
    ProjectStorageInfoGQL,
    ProjectTypeEnum,
    ProjectV2Connection,
    ProjectV2Edge,
    ProjectV2GQL,
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
    "ProjectTypeEnum",
    "VFolderHostPermissionEnum",
    # Nested types
    "ProjectBasicInfoGQL",
    "ProjectOrganizationInfoGQL",
    "VFolderHostPermissionEntryGQL",
    "ProjectStorageInfoGQL",
    "ProjectLifecycleInfoGQL",
    # Node types
    "ProjectV2GQL",
    "ProjectV2Edge",
    "ProjectV2Connection",
]
