"""Request DTOs for VFS Storage DTO v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.v2.common import NonEmptyList

__all__ = (
    "AdminSearchVFSStoragesInput",
    "CreateVFSStorageInput",
    "DeleteVFSStorageInput",
    "PartialBulkPurgeVFSStoragesInput",
    "PartialBulkUpdateVFSStoragesInput",
    "UpdateVFSStorageInput",
)


class CreateVFSStorageInput(BaseRequestModel):
    """Input for creating a VFS storage."""

    name: str = Field(description="Storage name")
    host: str = Field(description="Storage host address")
    base_path: str = Field(description="Base path on the storage host")


class UpdateVFSStorageInput(BaseRequestModel):
    """Input for updating a VFS storage."""

    id: UUID = Field(description="Storage ID to update")
    name: str | None = Field(default=None, description="Updated storage name")
    host: str | None = Field(default=None, description="Updated host address")
    base_path: str | None = Field(default=None, description="Updated base path")


class DeleteVFSStorageInput(BaseRequestModel):
    """Input for deleting a VFS storage."""

    id: UUID = Field(description="Storage ID to delete")


class PartialBulkUpdateVFSStoragesInput(BaseRequestModel):
    """Input for updating several VFS storages, each answered for separately."""

    items: NonEmptyList[UpdateVFSStorageInput] = Field(
        description="The VFS storages to update, each with its ID and fields."
    )


class PartialBulkPurgeVFSStoragesInput(BaseRequestModel):
    """Input for permanently purging several VFS storages, each answered for separately."""

    ids: NonEmptyList[UUID] = Field(description="IDs of the VFS storages to purge.")


class AdminSearchVFSStoragesInput(BaseRequestModel):
    """Input for searching VFS storages (admin, no scope)."""

    limit: int | None = Field(default=None, ge=1, description="Max results per page")
    offset: int | None = Field(default=None, ge=0, description="Pagination offset")
