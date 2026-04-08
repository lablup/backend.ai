"""VFolder GraphQL API package.

Provides structured vfolder management API with typed fields
replacing JSON scalars and organized into logical field groups.
"""

from .resolver import (
    admin_vfolders_v2,
    bulk_delete_vfolders_v2,
    bulk_purge_vfolders_v2,
    clone_vfolder_v2,
    create_vfolder_v2,
    delete_vfolder_v2,
    my_vfolders,
    project_vfolders,
    purge_vfolder_v2,
    vfolder_create_download_session_v2,
    vfolder_create_upload_session_v2,
    vfolder_delete_files_v2,
    vfolder_list_files_v2,
    vfolder_mkdir_v2,
    vfolder_move_file_v2,
    vfolder_v2,
)
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
    "admin_vfolders_v2",
    "my_vfolders",
    "project_vfolders",
    "vfolder_v2",
    # Mutations
    "bulk_delete_vfolders_v2",
    "bulk_purge_vfolders_v2",
    "create_vfolder_v2",
    "delete_vfolder_v2",
    "purge_vfolder_v2",
    "clone_vfolder_v2",
    "vfolder_list_files_v2",
    "vfolder_mkdir_v2",
    "vfolder_move_file_v2",
    "vfolder_delete_files_v2",
    "vfolder_create_upload_session_v2",
    "vfolder_create_download_session_v2",
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
