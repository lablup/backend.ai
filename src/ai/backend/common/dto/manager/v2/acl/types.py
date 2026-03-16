"""
Common types for acl DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import VFolderHostPermission

__all__ = (
    "PermissionListInfo",
    "VFolderHostPermission",
)


class PermissionListInfo(BaseResponseModel):
    """List of vfolder host permissions for embedding in ACL responses."""

    vfolder_host_permission_list: list[str] = Field(
        description="List of all available vfolder host permissions",
    )
