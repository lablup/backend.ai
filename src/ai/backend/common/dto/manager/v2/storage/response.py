"""
Response DTOs for storage DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "GetVFSStoragePayload",
    "ListVFSStoragePayload",
    "VFSStorageNode",
)


class VFSStorageNode(BaseResponseModel):
    """Node model representing a VFS storage entry."""

    name: str = Field(description="Storage name")
    base_path: str = Field(description="Base file system path of the storage")
    host: str = Field(description="Storage host identifier")


class GetVFSStoragePayload(BaseResponseModel):
    """Payload for single VFS storage retrieval result."""

    storage: VFSStorageNode = Field(description="VFS storage data")


class ListVFSStoragePayload(BaseResponseModel):
    """Payload for VFS storage list query result."""

    storages: list[VFSStorageNode] = Field(description="List of VFS storages")
