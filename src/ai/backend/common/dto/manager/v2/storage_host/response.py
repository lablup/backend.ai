"""
Response DTOs for storage host DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.storage_host.types import VFolderHostPermission

__all__ = (
    "MyStorageHostPermissionsPayload",
    "StorageHostPermissionNode",
)


class StorageHostPermissionNode(BaseResponseModel):
    """Read model representing a single storage host and its granted permissions."""

    host: str = Field(description="Storage host name.")
    permissions: list[VFolderHostPermission] = Field(
        description="Permissions granted to the current user on this storage host.",
    )


class MyStorageHostPermissionsPayload(BaseResponseModel):
    """Payload listing storage hosts the current user may access."""

    items: list[StorageHostPermissionNode] = Field(
        description="Storage hosts the current user is allowed to use.",
    )
