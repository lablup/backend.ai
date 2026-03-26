"""
Request DTOs for storage DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT

__all__ = (
    "GetVFSStorageInput",
    "ListVFSStorageInput",
    "VFSDownloadFileInput",
    "VFSListFilesInput",
)


class ListVFSStorageInput(BaseRequestModel):
    """Input for listing VFS storages with pagination."""

    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description="Maximum items to return",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class GetVFSStorageInput(BaseRequestModel):
    """Input for retrieving a single VFS storage by name."""

    storage_name: str = Field(description="Name of the VFS storage")


class VFSDownloadFileInput(BaseRequestModel):
    """Input for downloading a file from VFS storage."""

    filepath: str = Field(min_length=1, description="Path of the file to download")


class VFSListFilesInput(BaseRequestModel):
    """Input for listing files in a VFS storage directory."""

    directory: str = Field(min_length=1, description="Directory path to list files from")
