"""ProjectV2 GraphQL API package.

This package provides GraphQL API types for ProjectV2 (formerly GroupNode).
Types use structured field groups instead of JSON scalars.

Structure:
- types/: GraphQL type definitions (enums, nested types, nodes)
- resolver/: Query and mutation resolvers (future)
- fetcher/: Data loaders and fetchers (future)
"""

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
