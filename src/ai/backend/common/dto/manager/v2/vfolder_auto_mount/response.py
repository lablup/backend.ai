"""
Response DTOs for VFolderAutoMount v2 API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import MountPermission

__all__ = (
    "CreateVFolderAutoMountPayload",
    "DeleteVFolderAutoMountPayload",
    "SearchVFolderAutoMountsPayload",
    "UpdateVFolderAutoMountPayload",
    "VFolderAutoMountNode",
)


class VFolderAutoMountNode(BaseResponseModel):
    """A vfolder mounted into every session created in a project."""

    id: UUID = Field(description="ID of the auto-mount.")
    entity_id: UUID = Field(description="ID of the auto-mount.")
    project_id: UUID = Field(description="ID of the project the vfolder is auto-mounted in.")
    vfolder_id: UUID = Field(description="ID of the auto-mounted vfolder.")
    mount_destination: str = Field(
        description="Path in the session container the vfolder is mounted at."
    )
    subpath: str = Field(description="Path inside the vfolder that is mounted.")
    mount_permission: MountPermission = Field(description="Permission the vfolder is mounted with.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime = Field(description="Last update timestamp.")
    deleted_at: datetime | None = Field(
        default=None, description="Deletion timestamp. Null while the auto-mount is in use."
    )


class SearchVFolderAutoMountsPayload(BaseResponseModel):
    """Payload for paginated vfolder auto-mount search results."""

    items: list[VFolderAutoMountNode] = Field(description="List of auto-mount nodes.")
    total_count: int = Field(description="Total number of auto-mounts matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class CreateVFolderAutoMountPayload(BaseResponseModel):
    """Payload for a vfolder auto-mount creation."""

    vfolder_auto_mount: VFolderAutoMountNode = Field(description="The created auto-mount.")


class UpdateVFolderAutoMountPayload(BaseResponseModel):
    """Payload for a vfolder auto-mount update."""

    vfolder_auto_mount: VFolderAutoMountNode = Field(description="The updated auto-mount.")


class DeleteVFolderAutoMountPayload(BaseResponseModel):
    """Payload for a vfolder auto-mount deletion."""

    vfolder_auto_mount: VFolderAutoMountNode = Field(description="The auto-mount marked deleted.")
