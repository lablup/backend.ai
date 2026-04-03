"""VFolder GraphQL types package."""

from .enum import (
    VFolderHostPermissionGQL,
    VFolderMountPermissionGQL,
    VFolderOperationStatusGQL,
    VFolderOwnershipTypeGQL,
    VFolderUsageModeGQL,
)
from .filters import (
    HostPermissionConditionGQL,
    VFolderFilterGQL,
    VFolderOperationStatusFilterGQL,
    VFolderOrderByGQL,
    VFolderOrderFieldGQL,
    VFolderUsageModeFilterGQL,
)
from .nested import (
    VFolderAccessControlInfoGQL,
    VFolderMetadataInfoGQL,
    VFolderOwnershipInfoGQL,
)
from .node import VFolderConnection, VFolderEdge, VFolderGQL

__all__ = [
    # Enum types
    "VFolderUsageModeGQL",
    "VFolderMountPermissionGQL",
    "VFolderOwnershipTypeGQL",
    "VFolderOperationStatusGQL",
    "VFolderHostPermissionGQL",
    # Enum filters
    "VFolderOperationStatusFilterGQL",
    "VFolderUsageModeFilterGQL",
    "HostPermissionConditionGQL",
    # Filter and OrderBy
    "VFolderFilterGQL",
    "VFolderOrderByGQL",
    "VFolderOrderFieldGQL",
    # Nested types
    "VFolderMetadataInfoGQL",
    "VFolderAccessControlInfoGQL",
    "VFolderOwnershipInfoGQL",
    # Node types
    "VFolderGQL",
    "VFolderEdge",
    "VFolderConnection",
]
