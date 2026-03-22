"""
Response DTOs for vfolder DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import (
    VFolderBasicInfo,
    VFolderInvitationState,
    VFolderOwnerInfo,
    VFolderPermissionField,
    VFolderPermissionInfo,
    VFolderUsageInfo,
)

__all__ = (
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
    "PurgeVFolderPayload",
    "RestoreVFolderPayload",
    "ShareVFolderPayload",
    "UnshareVFolderPayload",
    "UpdateVFolderPayload",
    "VFolderCompactNode",
    "VFolderInvitationNode",
    "VFolderNode",
)


# ============================================================
# Node Models
# ============================================================


class VFolderNode(BaseResponseModel):
    """Node model representing a virtual folder entity with nested sub-models."""

    basic: VFolderBasicInfo = Field(description="Core identity fields")
    permission: VFolderPermissionInfo = Field(description="Permission and ownership fields")
    owner: VFolderOwnerInfo = Field(description="Owner context fields")
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
    type: str = Field(description="Entry type (file or directory)")
    size: int = Field(description="File size in bytes")
    mode: str = Field(description="File permission mode string")
    created: str = Field(description="Creation timestamp string")
    modified: str = Field(description="Last modification timestamp string")


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


class DeleteFilesPayload(BaseResponseModel):
    """Payload for file deletion mutation result."""

    bgtask_id: str | None = Field(
        default=None, description="Background task ID if deletion is async"
    )


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
