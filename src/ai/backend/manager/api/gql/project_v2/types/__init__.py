"""ProjectV2 GraphQL types package."""

from .enums import ProjectTypeEnum, VFolderHostPermissionEnum
from .nested import (
    ProjectBasicInfoGQL,
    ProjectLifecycleInfoGQL,
    ProjectOrganizationInfoGQL,
    ProjectStorageInfoGQL,
    VFolderHostPermissionEntryGQL,
)
from .node import ProjectV2Connection, ProjectV2Edge, ProjectV2GQL

__all__ = [
    # Enums
    "ProjectTypeEnum",
    "VFolderHostPermissionEnum",
    # Nested types - Basic
    "ProjectBasicInfoGQL",
    # Nested types - Organization
    "ProjectOrganizationInfoGQL",
    # Nested types - Storage
    "VFolderHostPermissionEntryGQL",
    "ProjectStorageInfoGQL",
    # Nested types - Lifecycle
    "ProjectLifecycleInfoGQL",
    # Node types
    "ProjectV2GQL",
    "ProjectV2Edge",
    "ProjectV2Connection",
]
