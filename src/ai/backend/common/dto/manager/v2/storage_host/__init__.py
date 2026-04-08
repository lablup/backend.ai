"""
Storage host DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.storage_host.response import (
    MyStorageHostPermissionsPayload,
    StorageHostPermissionNode,
)
from ai.backend.common.dto.manager.v2.storage_host.types import VFolderHostPermission

__all__ = (
    "MyStorageHostPermissionsPayload",
    "StorageHostPermissionNode",
    "VFolderHostPermission",
)
