"""
Response DTOs for vfolder DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import (
    FileEntryType,
    VFolderAccessControlInfo,
    VFolderInvitationState,
    VFolderMetadataInfo,
    VFolderOperationStatusField,
    VFolderOwnershipInfo,
    VFolderPermissionField,
    VFolderUsageInfo,
)

__all__ = (
    "BulkDeleteVFoldersPayload",
    "BulkPurgeVFoldersPayload",
    "CloneVFolderPayload",
    "CreateDownloadSessionPayload",
    "CreateUploadSessionPayload",
    "CreateVFolderPayload",
    "DeleteFilesPayload",
    "DeleteVFolderPayload",
    "FileEntryNode",
    "InviteVFolderPayload",
    "ListFilesPayload",
    "MkdirPayload",
    "MoveFilePayload",
    "PurgeVFolderPayload",
    "RestoreVFolderPayload",
    "ShareVFolderPayload",
    "UnshareVFolderPayload",
    "UpdateVFolderPayload",
    "VFolderCompactNode",
    "VFolderInvitationNode",
    "VFolderNode",
    "SearchVFoldersPayload",
)


# ============================================================
# Node Models
# ============================================================


class VFolderNode(BaseResponseModel):
    """Node model representing a virtual folder entity with nested sub-models."""

    id: UUID = Field(description="Unique identifier of the virtual folder")
    status: VFolderOperationStatusField = Field(description="Current operation status")
    host: str = Field(description="Storage host where the virtual folder is located")
    metadata: VFolderMetadataInfo = Field(description="Descriptive metadata fields")
    access_control: VFolderAccessControlInfo = Field(description="Access control fields")
    ownership: VFolderOwnershipInfo = Field(description="Ownership context fields")
    usage: VFolderUsageInfo | None = Field(
        default=None,
        description="Usage statistics; None for list responses where usage is not loaded",
    )
    unmanaged_path: str | None = Field(
        default=None, description="Path for unmanaged virtual folders"
    )


class VFolderCompactNode(BaseResponseModel):
    """Compact node model for lightweight vfolder references."""

    id: UUID = Field(description="VFolder ID")
    name: str = Field(description="VFolder name")


class VFolderInvitationNode(BaseResponseModel):
    """Node model representing a virtual folder invitation."""

    id: UUID = Field(description="Invitation ID")
    vfolder_id: UUID = Field(description="ID of the virtual folder being invited to")
    vfolder_name: str = Field(description="Name of the virtual folder")
    inviter: str = Field(description="Email of the inviter")
    invitee: str = Field(description="Email of the invitee")
    permission: VFolderPermissionField = Field(description="Permission level granted by invitation")
    state: VFolderInvitationState = Field(description="Current state of the invitation")
    created_at: datetime = Field(description="Invitation creation timestamp")
    modified_at: datetime | None = Field(
        default=None, description="Last modification timestamp of the invitation"
    )


class FileEntryNode(BaseResponseModel):
    """Node model representing a file entry inside a virtual folder."""

    name: str = Field(description="File or directory name")
    type: FileEntryType = Field(description="Entry type")
    size: int = Field(description="File size in bytes")
    mode: int = Field(description="POSIX file permission mode (e.g., 33188 for 0o100644)")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last modification timestamp")


# ============================================================
# CRUD Payload Models
# ============================================================


class CreateVFolderPayload(BaseResponseModel):
    """Payload for virtual folder creation mutation result."""

    vfolder: VFolderNode = Field(description="Created virtual folder")


class UpdateVFolderPayload(BaseResponseModel):
    """Payload for virtual folder update mutation result."""

    vfolder: VFolderNode = Field(description="Updated virtual folder")


class DeleteVFolderPayload(BaseResponseModel):
    """Payload for virtual folder soft-deletion mutation result."""

    id: UUID = Field(description="ID of the deleted virtual folder")


class PurgeVFolderPayload(BaseResponseModel):
    """Payload for virtual folder purge mutation result."""

    id: UUID = Field(description="ID of the purged virtual folder")


class BulkDeleteVFoldersPayload(BaseResponseModel):
    """Payload for bulk virtual folder soft-deletion."""

    deleted_count: int = Field(description="Number of virtual folders successfully soft-deleted.")


class BulkPurgeVFoldersPayload(BaseResponseModel):
    """Payload for bulk virtual folder purge."""

    purged_count: int = Field(description="Number of virtual folders successfully purged.")


class RestoreVFolderPayload(BaseResponseModel):
    """Payload for virtual folder restore mutation result."""

    id: UUID = Field(description="ID of the restored virtual folder")


class CloneVFolderPayload(BaseResponseModel):
    """Payload for virtual folder clone mutation result."""

    vfolder: VFolderNode = Field(description="Cloned virtual folder")
    bgtask_id: str = Field(description="Background task ID for the clone operation")


# ============================================================
# File Operation Payload Models
# ============================================================


class MkdirPayload(BaseResponseModel):
    """Payload for directory creation mutation result."""

    results: list[str] = Field(description="List of created directory paths")


class CreateDownloadSessionPayload(BaseResponseModel):
    """Payload for download session creation mutation result."""

    token: str = Field(description="Download session token")
    url: str = Field(description="Download URL")


class CreateUploadSessionPayload(BaseResponseModel):
    """Payload for upload session creation mutation result."""

    token: str = Field(description="Upload session token")
    url: str = Field(description="Upload URL")


class MoveFilePayload(BaseResponseModel):
    """Payload for file move mutation result."""

    src: str = Field(description="Source path that was moved")
    dst: str = Field(description="Destination path")


class DeleteFilesPayload(BaseResponseModel):
    """Payload for async file deletion. Always runs as a background task."""

    bgtask_id: str = Field(description="Background task ID for the deletion operation")


class ListFilesPayload(BaseResponseModel):
    """Payload for file listing query result."""

    items: list[FileEntryNode] = Field(description="List of file entries")


# ============================================================
# Sharing Payload Models
# ============================================================


class InviteVFolderPayload(BaseResponseModel):
    """Payload for virtual folder invitation mutation result."""

    invited_ids: list[str] = Field(description="List of invitation IDs created")


class ShareVFolderPayload(BaseResponseModel):
    """Payload for virtual folder share mutation result."""

    shared_emails: list[str] = Field(description="List of email addresses that were shared with")


class UnshareVFolderPayload(BaseResponseModel):
    """Payload for virtual folder unshare mutation result."""

    unshared_emails: list[str] = Field(
        description="List of email addresses that were unshared from"
    )


# ============================================================
# Search Payload Models
# ============================================================


class SearchVFoldersPayload(BaseResponseModel):
    """Payload for vfolder search (shared by admin and scoped searches)."""

    items: list[VFolderNode] = Field(description="List of vfolder nodes.")
    total_count: int = Field(description="Total number of records matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
