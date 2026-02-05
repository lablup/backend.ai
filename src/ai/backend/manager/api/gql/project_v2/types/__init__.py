"""ProjectV2 GraphQL types package."""

from .enums import ProjectTypeEnum, VFolderHostPermissionEnum
from .filters import ProjectV2Filter, ProjectV2OrderBy, ProjectV2OrderField
from .nested import (
    ProjectBasicInfoGQL,
    ProjectLifecycleInfoGQL,
    ProjectOrganizationInfoGQL,
    ProjectStorageInfoGQL,
    VFolderHostPermissionEntryGQL,
)
from .node import ProjectV2Connection, ProjectV2Edge, ProjectV2GQL
from .scopes import DomainProjectScope

__all__ = [
    # Enums
    "ProjectTypeEnum",
    "VFolderHostPermissionEnum",
    # Filters and OrderBy
    "ProjectV2Filter",
    "ProjectV2OrderBy",
    "ProjectV2OrderField",
    # Scopes
    "DomainProjectScope",
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
