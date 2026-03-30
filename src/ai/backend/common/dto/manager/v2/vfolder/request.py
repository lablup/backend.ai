"""
Request DTOs for vfolder DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter
from ai.backend.common.typed_validators import VFolderName

from .types import (
    OrderDirection,
    VFolderOrderField,
    VFolderPermissionField,
    VFolderStatusFilter,
    VFolderUsageMode,
    VFolderUsageModeFilter,
)

__all__ = (
    "AcceptInvitationInput",
    "CloneVFolderInput",
    "CreateDownloadSessionInput",
    "CreateUploadSessionInput",
    "CreateVFolderInput",
    "DeleteFilesInput",
    "DeleteInvitationInput",
    "DeleteVFolderInput",
    "InviteVFolderInput",
    "ListFilesInput",
    "MkdirInput",
    "MoveFileInput",
    "PurgeVFolderInput",
    "RenameFileInput",
    "RestoreVFolderInput",
    "ShareVFolderInput",
    "UnshareVFolderInput",
    "UpdateVFolderInput",
    "VFolderFilter",
    "VFolderOrder",
)


# ============================================================
# CRUD Operations
# ============================================================


class CreateVFolderInput(BaseRequestModel):
    """Input for creating a virtual folder."""

    name: VFolderName = Field(description="VFolder name")
    host: str | None = Field(default=None, description="Storage host for the vfolder")
    usage_mode: VFolderUsageMode = Field(
        default=VFolderUsageMode.GENERAL, description="Usage mode of the vfolder"
    )
    permission: VFolderPermissionField = Field(
        default=VFolderPermissionField.READ_WRITE,
        description="Default permission of the vfolder",
    )
    group_id: UUID | None = Field(default=None, description="Group ID for group-owned vfolder")
    cloneable: bool = Field(default=False, description="Whether the vfolder is cloneable")
    unmanaged_path: str | None = Field(default=None, description="Path for unmanaged vfolders")

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("name must not be blank or whitespace-only")
            return stripped
        return v


class UpdateVFolderInput(BaseRequestModel):
    """Input for updating a virtual folder."""

    name: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated vfolder name. Use SENTINEL (default) for no change.",
    )
    cloneable: bool | None = Field(default=None, description="Updated cloneable setting")
    permission: VFolderPermissionField | None = Field(
        default=None, description="Updated permission level"
    )

    @field_validator("name")
    @classmethod
    def strip_and_validate_name(cls, v: str | Sentinel | None) -> str | Sentinel | None:
        if v is None or isinstance(v, Sentinel):
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class DeleteVFolderInput(BaseRequestModel):
    """Input for soft-deleting a virtual folder."""

    id: UUID = Field(description="VFolder ID to delete")


class PurgeVFolderInput(BaseRequestModel):
    """Input for purging a virtual folder."""

    id: UUID = Field(description="VFolder ID to purge")


class RestoreVFolderInput(BaseRequestModel):
    """Input for restoring a virtual folder from trash."""

    id: UUID = Field(description="VFolder ID to restore")


class CloneVFolderInput(BaseRequestModel):
    """Input for cloning a virtual folder."""

    source_id: UUID = Field(description="Source vfolder ID to clone")
    target_name: str = Field(
        min_length=1, max_length=256, description="Name for the cloned vfolder"
    )
    target_host: str | None = Field(default=None, description="Target host for the clone")
    usage_mode: VFolderUsageMode = Field(
        default=VFolderUsageMode.GENERAL, description="Usage mode of the cloned vfolder"
    )
    permission: VFolderPermissionField = Field(
        default=VFolderPermissionField.READ_WRITE,
        description="Permission level of the cloned vfolder",
    )
    cloneable: bool = Field(default=False, description="Whether the cloned vfolder is cloneable")

    @field_validator("target_name")
    @classmethod
    def strip_and_validate_target_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("target_name must not be blank or whitespace-only")
        return stripped


# ============================================================
# File Operation Inputs
# ============================================================


class MkdirInput(BaseRequestModel):
    """Input for creating directories inside a virtual folder."""

    path: str | list[str] = Field(description="Directory path(s) to create")
    parents: bool = Field(default=True, description="Create parent directories if needed")
    exist_ok: bool = Field(default=False, description="Do not raise error if directory exists")


class CreateDownloadSessionInput(BaseRequestModel):
    """Input for creating a file download session."""

    path: str = Field(description="File path to download")
    archive: bool = Field(default=False, description="Whether to archive the file for download")


class CreateUploadSessionInput(BaseRequestModel):
    """Input for creating a file upload session."""

    path: str = Field(description="File path to upload to")
    size: int = Field(ge=0, description="File size in bytes")


class RenameFileInput(BaseRequestModel):
    """Input for renaming a file inside a virtual folder."""

    target_path: str = Field(description="Path of the file to rename")
    new_name: str = Field(min_length=1, description="New name for the file")


class MoveFileInput(BaseRequestModel):
    """Input for moving a file inside a virtual folder."""

    src: str = Field(description="Source file path")
    dst: str = Field(description="Destination file path")


class DeleteFilesInput(BaseRequestModel):
    """Input for deleting files inside a virtual folder."""

    files: list[str] = Field(min_length=1, description="List of file paths to delete")
    recursive: bool = Field(default=False, description="Whether to delete directories recursively")


class ListFilesInput(BaseRequestModel):
    """Input for listing files in a virtual folder."""

    path: str = Field(default="", description="Directory path to list files from")


# ============================================================
# Sharing/Invitation Inputs
# ============================================================


class InviteVFolderInput(BaseRequestModel):
    """Input for inviting users to a virtual folder."""

    permission: VFolderPermissionField = Field(
        default=VFolderPermissionField.READ_WRITE,
        description="Permission level for invitees",
    )
    emails: list[str] = Field(min_length=1, description="Email addresses of users to invite")


class ShareVFolderInput(BaseRequestModel):
    """Input for sharing a virtual folder with users."""

    permission: VFolderPermissionField = Field(
        default=VFolderPermissionField.READ_WRITE,
        description="Permission level for shared users",
    )
    emails: list[str] = Field(description="Email addresses of users to share with")


class UnshareVFolderInput(BaseRequestModel):
    """Input for unsharing a virtual folder from users."""

    emails: list[str] = Field(description="Email addresses of users to unshare from")


class AcceptInvitationInput(BaseRequestModel):
    """Input for accepting a virtual folder invitation."""

    invitation_id: UUID = Field(description="Invitation ID to accept")


class DeleteInvitationInput(BaseRequestModel):
    """Input for deleting a virtual folder invitation."""

    invitation_id: UUID = Field(description="Invitation ID to delete")


# ============================================================
# Search / Filter / Order
# ============================================================


class VFolderFilter(BaseRequestModel):
    """Filter criteria for searching virtual folders."""

    name: StringFilter | None = Field(default=None, description="Filter by vfolder name.")
    host: StringFilter | None = Field(default=None, description="Filter by storage host.")
    status: VFolderStatusFilter | None = Field(
        default=None, description="Filter by operation status."
    )
    usage_mode: VFolderUsageModeFilter | None = Field(
        default=None, description="Filter by usage mode."
    )
    created_at: DateTimeFilter | None = Field(default=None, description="Filter by creation time.")
    AND: list[VFolderFilter] | None = Field(default=None, description="AND logical combinator.")
    OR: list[VFolderFilter] | None = Field(default=None, description="OR logical combinator.")
    NOT: list[VFolderFilter] | None = Field(default=None, description="NOT logical combinator.")


VFolderFilter.model_rebuild()


class VFolderOrder(BaseRequestModel):
    """Order specification for virtual folder search results."""

    field: VFolderOrderField
    direction: OrderDirection
