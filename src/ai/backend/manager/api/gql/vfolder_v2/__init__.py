"""VFolderV2 GraphQL API package.

Provides structured vfolder management API with typed fields
replacing JSON scalars and organized into logical field groups.
"""

from .resolver import project_vfolders_v2
from .types import (
    VFolderAccessControlInfoGQL,
    VFolderMetadataInfoGQL,
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
    # Queries
    "project_vfolders_v2",
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
    "VFolderMetadataInfoGQL",
    "VFolderAccessControlInfoGQL",
    "VFolderUsageInfoGQL",
    # Node types
    "VFolderV2GQL",
    "VFolderV2Edge",
    "VFolderV2Connection",
]
