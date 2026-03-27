"""VFolderV2 GraphQL API package.

Provides structured vfolder management API with typed fields
replacing JSON scalars and organized into logical field groups.
"""

from .types import (
    VFolderBasicInfoGQL,
    VFolderOwnerInfoGQL,
    VFolderPermissionInfoGQL,
    VFolderUsageInfoGQL,
    VFolderV2Connection,
    VFolderV2Edge,
    VFolderV2FilterGQL,
    VFolderV2GQL,
    VFolderV2OperationStatusFilterGQL,
    VFolderV2OperationStatusGQL,
    VFolderV2OrderByGQL,
    VFolderV2OrderFieldGQL,
    VFolderV2UsageModeFilterGQL,
    VFolderV2UsageModeGQL,
)

__all__ = [
    # Enum types
    "VFolderV2OperationStatusGQL",
    "VFolderV2UsageModeGQL",
    # Enum filters
    "VFolderV2OperationStatusFilterGQL",
    "VFolderV2UsageModeFilterGQL",
    # Filter and OrderBy
    "VFolderV2FilterGQL",
    "VFolderV2OrderByGQL",
    "VFolderV2OrderFieldGQL",
    # Nested types
    "VFolderBasicInfoGQL",
    "VFolderPermissionInfoGQL",
    "VFolderOwnerInfoGQL",
    "VFolderUsageInfoGQL",
    # Node types
    "VFolderV2GQL",
    "VFolderV2Edge",
    "VFolderV2Connection",
]
