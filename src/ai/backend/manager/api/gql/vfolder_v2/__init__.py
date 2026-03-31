"""VFolder GraphQL API package.

Provides structured vfolder management API with typed fields
replacing JSON scalars and organized into logical field groups.
"""

from .resolver import my_vfolders_v2, project_vfolders
from .types import (
    VFolderAccessControlInfoGQL,
    VFolderConnection,
    VFolderEdge,
    VFolderFilterGQL,
    VFolderGQL,
    VFolderMetadataInfoGQL,
    VFolderOperationStatusFilterGQL,
    VFolderOperationStatusGQL,
    VFolderOrderByGQL,
    VFolderOrderFieldGQL,
    VFolderUsageModeFilterGQL,
    VFolderUsageModeGQL,
)

__all__ = [
    # Queries
    "my_vfolders_v2",
    "project_vfolders",
    # Enum types
    "VFolderOperationStatusGQL",
    "VFolderUsageModeGQL",
    # Enum filters
    "VFolderOperationStatusFilterGQL",
    "VFolderUsageModeFilterGQL",
    # Filter and OrderBy
    "VFolderFilterGQL",
    "VFolderOrderByGQL",
    "VFolderOrderFieldGQL",
    # Nested types
    "VFolderMetadataInfoGQL",
    "VFolderAccessControlInfoGQL",
    # Node types
    "VFolderGQL",
    "VFolderEdge",
    "VFolderConnection",
]
