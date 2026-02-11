"""ProjectV2 GraphQL types package."""

from .enums import ProjectV2TypeEnum, VFolderHostPermissionEnum
from .filters import (
    ProjectV2DomainNestedFilter,
    ProjectV2Filter,
    ProjectV2OrderBy,
    ProjectV2OrderField,
    ProjectV2UserNestedFilter,
)
from .nested import (
    ProjectV2BasicInfoGQL,
    ProjectV2LifecycleInfoGQL,
    ProjectV2OrganizationInfoGQL,
    ProjectV2StorageInfoGQL,
    VFolderHostPermissionEntryGQL,
)
from .node import ProjectV2Connection, ProjectV2Edge, ProjectV2GQL
from .scopes import DomainProjectV2Scope

__all__ = [
    # Enums
    "ProjectV2TypeEnum",
    "VFolderHostPermissionEnum",
    # Filters and OrderBy
    "ProjectV2DomainNestedFilter",
    "ProjectV2UserNestedFilter",
    "ProjectV2Filter",
    "ProjectV2OrderBy",
    "ProjectV2OrderField",
    # Scopes
    "DomainProjectV2Scope",
    # Nested types - Basic
    "ProjectV2BasicInfoGQL",
    # Nested types - Organization
    "ProjectV2OrganizationInfoGQL",
    # Nested types - Storage
    "VFolderHostPermissionEntryGQL",
    "ProjectV2StorageInfoGQL",
    # Nested types - Lifecycle
    "ProjectV2LifecycleInfoGQL",
    # Node types
    "ProjectV2GQL",
    "ProjectV2Edge",
    "ProjectV2Connection",
]
