"""
ACL DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.acl.response import (
    GetPermissionsPayload,
)
from ai.backend.common.dto.manager.v2.acl.types import (
    PermissionListInfo,
    VFolderHostPermission,
)

__all__ = (
    # Types
    "PermissionListInfo",
    "VFolderHostPermission",
    # Payload models (response)
    "GetPermissionsPayload",
)
