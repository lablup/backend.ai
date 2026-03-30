"""Response DTOs for VFS Storage DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AdminSearchVFSStoragesPayload",
    "CreateVFSStoragePayload",
    "DeleteVFSStoragePayload",
    "UpdateVFSStoragePayload",
    "VFSStorageNode",
)


class VFSStorageNode(BaseResponseModel):
    """Node model representing a VFS storage."""

    id: UUID = Field(description="Storage ID")
    name: str = Field(description="Storage name")
    host: str = Field(description="Storage host address")
    base_path: str = Field(description="Base path on the storage host")


class CreateVFSStoragePayload(BaseResponseModel):
    """Payload for VFS storage creation mutation result."""

    vfs_storage: VFSStorageNode = Field(description="Created VFS storage")


class UpdateVFSStoragePayload(BaseResponseModel):
    """Payload for VFS storage update mutation result."""

    vfs_storage: VFSStorageNode = Field(description="Updated VFS storage")


class DeleteVFSStoragePayload(BaseResponseModel):
    """Payload for VFS storage deletion mutation result."""

    id: UUID = Field(description="ID of the deleted VFS storage")


class AdminSearchVFSStoragesPayload(BaseResponseModel):
    """Payload for VFS storage search result."""

    items: list[VFSStorageNode] = Field(description="VFS storage list")
    total_count: int = Field(description="Total count")
    has_next_page: bool = Field(description="Whether a next page exists")
    has_previous_page: bool = Field(description="Whether a previous page exists")
