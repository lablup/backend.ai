"""
Request DTOs for VFolder API endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.field import VFolderPermissionField
from ai.backend.common.typed_validators import VFolderName
from ai.backend.common.types import VFolderUsageMode

__all__ = (
    # CRUD Operations
    "CloneVFolderReq",
    "DeleteVFolderByIDReq",
    "DeleteVFolderFromTrashReq",
    "GetVFolderIDReq",
    "PurgeVFolderReq",
    "RenameVFolderReq",
    "RestoreVFolderReq",
    "UpdateVFolderOptionsReq",
    "VFolderCreateReq",
    # List/Query Operations
    "ListSharedVFoldersQuery",
    "ListVFoldersQuery",
    # File Operations
    "CreateDownloadSessionReq",
    "CreateUploadSessionReq",
    "DeleteFilesAsyncBodyParam",
    "DeleteFilesAsyncPathParam",
    "DeleteFilesReq",
    "ListFilesQuery",
    "MkdirReq",
    "MoveFileReq",
    "RenameFileReq",
    # Sharing/Invitation Operations
    "AcceptInvitationReq",
    "DeleteInvitationReq",
    "InviteVFolderReq",
    "LeaveVFolderReq",
    "ShareVFolderReq",
    "UnshareVFolderReq",
    "UpdateInvitationReq",
    "UpdateSharedVFolderReq",
    "UpdateVFolderSharingStatusReq",
    "UserPermMapping",
    # Admin Operations
    "ChangeVFolderOwnershipReq",
    "GetFstabContentsQuery",
    "GetQuotaQuery",
    "GetUsageQuery",
    "GetUsedBytesQuery",
    "GetVolumePerfMetricQuery",
    "ListHostsQuery",
    "MountHostReq",
    "UmountHostReq",
    "UpdateQuotaReq",
)


# ============================================================
# CRUD Operations
# ============================================================


class VFolderCreateReq(BaseRequestModel):
    """Request to create a new virtual folder."""

    name: VFolderName = Field(description="Name of the vfolder")
    folder_host: str | None = Field(default=None, alias="host")
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermissionField = Field(default=VFolderPermissionField.READ_WRITE)
    unmanaged_path: str | None = Field(default=None, alias="unmanagedPath")
    group_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("group", "groupId"),
    )
    cloneable: bool = Field(default=False)


class RenameVFolderReq(BaseRequestModel):
    """Request to rename a virtual folder."""

    new_name: VFolderName = Field(description="Name of the vfolder")


class UpdateVFolderOptionsReq(BaseRequestModel):
    """Request to update virtual folder options."""

    cloneable: bool | None = Field(default=None, description="Whether the vfolder is cloneable")
    permission: VFolderPermissionField | None = Field(
        default=None, description="Permission level of the vfolder"
    )


class DeleteVFolderByIDReq(BaseRequestModel):
    """Request to delete a virtual folder by ID."""

    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("vfolderId", "id"),
        description="VFolder ID to delete",
    )


class DeleteVFolderFromTrashReq(BaseRequestModel):
    """Request to permanently delete a virtual folder from trash."""

    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("id", "vfolderId"),
        description="VFolder ID to delete from trash",
    )


class PurgeVFolderReq(BaseRequestModel):
    """Request to purge a virtual folder."""

    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("id", "vfolderId"),
        description="VFolder ID to purge",
    )


class RestoreVFolderReq(BaseRequestModel):
    """Request to restore a virtual folder from trash."""

    vfolder_id: uuid.UUID = Field(
        validation_alias=AliasChoices("id", "vfolderId"),
        description="VFolder ID to restore",
    )


class CloneVFolderReq(BaseRequestModel):
    """Request to clone a virtual folder."""

    target_name: str = Field(description="Name for the cloned vfolder")
    target_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices("target_host", "folder_host"),
        description="Target host for the clone",
    )
    cloneable: bool = Field(default=False, description="Whether the cloned vfolder is cloneable")
    usage_mode: VFolderUsageMode = Field(default=VFolderUsageMode.GENERAL)
    permission: VFolderPermissionField = Field(default=VFolderPermissionField.READ_WRITE)


class GetVFolderIDReq(BaseRequestModel):
    """Request to get a vfolder ID by name."""

    name: str = Field(
        validation_alias=AliasChoices("vfolder_name", "vfolderName"),
        description="VFolder name to look up",
    )


# ============================================================
# List/Query Operations
# ============================================================


class ListVFoldersQuery(BaseRequestModel):
    """Query parameters for listing virtual folders."""

    all: bool = Field(default=False, description="List all vfolders regardless of ownership")
    group_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("group_id", "groupId"),
        description="Filter by group ID",
    )
    owner_user_email: str | None = Field(
        default=None,
        validation_alias=AliasChoices("owner_user_email", "ownerUserEmail"),
        description="Filter by owner email",
    )


class ListSharedVFoldersQuery(BaseRequestModel):
    """Query parameters for listing shared virtual folders."""

    vfolder_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("vfolder_id", "vfolderId"),
        description="Filter by specific vfolder ID",
    )


# ============================================================
# File Operations
# ============================================================


class MkdirReq(BaseRequestModel):
    """Request to create directories inside a virtual folder."""

    path: str | list[str] = Field(description="Directory path(s) to create")
    parents: bool = Field(default=True, description="Create parent directories if needed")
    exist_ok: bool = Field(default=False, description="Do not raise error if directory exists")


class CreateDownloadSessionReq(BaseRequestModel):
    """Request to create a file download session."""

    path: str = Field(
        validation_alias=AliasChoices("path", "file"),
        description="File path to download",
    )
    archive: bool = Field(default=False, description="Whether to archive the file for download")


class CreateUploadSessionReq(BaseRequestModel):
    """Request to create a file upload session."""

    path: str = Field(description="File path to upload to")
    size: int = Field(description="File size in bytes")


class RenameFileReq(BaseRequestModel):
    """Request to rename a file inside a virtual folder."""

    target_path: str = Field(description="Path of the file to rename")
    new_name: str = Field(description="New name for the file")
    is_dir: bool = Field(default=False, description="Whether the target is a directory (ignored)")


class MoveFileReq(BaseRequestModel):
    """Request to move a file inside a virtual folder."""

    src: str = Field(description="Source file path")
    dst: str = Field(description="Destination file path")


class DeleteFilesReq(BaseRequestModel):
    """Request to delete files inside a virtual folder."""

    files: list[str] = Field(description="List of file paths to delete")
    recursive: bool = Field(default=False, description="Whether to delete directories recursively")


class DeleteFilesAsyncPathParam(BaseRequestModel):
    """Path parameter for delete_files_async endpoint."""

    name: str = Field(description="VFolder name or ID to resolve")


class DeleteFilesAsyncBodyParam(BaseRequestModel):
    """Body parameter for delete_files_async endpoint."""

    files: list[str] = Field(
        description=(
            "List of file paths to delete within the vfolder. "
            "Paths are relative to the vfolder root."
        ),
    )
    recursive: bool = Field(
        default=False,
        description=(
            "Whether to delete directories recursively. "
            "Set to True when deleting non-empty directories."
        ),
    )


class ListFilesQuery(BaseRequestModel):
    """Query parameters for listing files in a virtual folder."""

    path: str = Field(default="", description="Directory path to list files from")


# ============================================================
# Sharing/Invitation Operations
# ============================================================


class InviteVFolderReq(BaseRequestModel):
    """Request to invite users to a virtual folder."""

    permission: VFolderPermissionField = Field(
        default=VFolderPermissionField.READ_WRITE,
        validation_alias=AliasChoices("perm", "permission"),
        description="Permission level for invitees",
    )
    emails: list[str] = Field(
        validation_alias=AliasChoices("emails", "user_ids", "userIDs"),
        description="Email addresses of users to invite",
    )


class AcceptInvitationReq(BaseRequestModel):
    """Request to accept a virtual folder invitation."""

    inv_id: str = Field(description="Invitation ID to accept")


class DeleteInvitationReq(BaseRequestModel):
    """Request to delete a virtual folder invitation."""

    inv_id: str = Field(description="Invitation ID to delete")


class UpdateInvitationReq(BaseRequestModel):
    """Request to update a virtual folder invitation permission."""

    permission: VFolderPermissionField = Field(
        validation_alias=AliasChoices("perm", "permission"),
        description="New permission level",
    )


class ShareVFolderReq(BaseRequestModel):
    """Request to share a virtual folder with users."""

    permission: VFolderPermissionField = Field(
        default=VFolderPermissionField.READ_WRITE,
        description="Permission level for shared users",
    )
    emails: list[str] = Field(description="Email addresses of users to share with")


class UnshareVFolderReq(BaseRequestModel):
    """Request to unshare a virtual folder from users."""

    emails: list[str] = Field(description="Email addresses of users to unshare from")


class UpdateSharedVFolderReq(BaseRequestModel):
    """Request to update shared virtual folder permission for a user."""

    vfolder: uuid.UUID = Field(description="VFolder ID")
    user: uuid.UUID = Field(description="User ID")
    permission: VFolderPermissionField | None = Field(
        default=None,
        validation_alias=AliasChoices("perm", "permission"),
        description="New permission level (None to remove)",
    )


class UserPermMapping(BaseRequestModel):
    """Mapping of user ID to permission for batch sharing status updates."""

    user_id: uuid.UUID = Field(description="User ID")
    perm: VFolderPermissionField | None = Field(
        default=None, description="Permission level (None to remove)"
    )


class UpdateVFolderSharingStatusReq(BaseRequestModel):
    """Request to batch update virtual folder sharing permissions."""

    vfolder_id: uuid.UUID = Field(
        alias="vfolder",
        description="VFolder ID",
    )
    user_perm_list: list[UserPermMapping] = Field(
        validation_alias=AliasChoices("user_perm", "userPermList"),
        description="List of user-permission mappings",
    )


class LeaveVFolderReq(BaseRequestModel):
    """Request to leave a shared virtual folder."""

    shared_user_uuid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("shared_user_uuid", "sharedUserUuid"),
        description="Shared user UUID (for admin leaving on behalf of another user)",
    )


# ============================================================
# Admin Operations
# ============================================================


class ListHostsQuery(BaseRequestModel):
    """Query parameters for listing vfolder hosts."""

    group_id: uuid.UUID | None = Field(
        default=None,
        validation_alias=AliasChoices("group_id", "groupId"),
        description="Filter by group ID",
    )


class GetVolumePerfMetricQuery(BaseRequestModel):
    """Query parameters for getting volume performance metrics."""

    folder_host: str = Field(description="Folder host to get metrics for")


class GetQuotaQuery(BaseRequestModel):
    """Query parameters for getting quota information."""

    folder_host: str = Field(description="Folder host")
    id: uuid.UUID = Field(description="Quota scope ID")


class UpdateQuotaReq(BaseRequestModel):
    """Request to update quota for a folder host."""

    folder_host: str = Field(description="Folder host")
    id: uuid.UUID = Field(description="Quota scope ID")
    input: dict[str, Any] = Field(description="Quota update input containing size_bytes")


class GetUsageQuery(BaseRequestModel):
    """Query parameters for getting usage information."""

    folder_host: str = Field(description="Folder host")
    id: uuid.UUID = Field(description="Quota scope ID")


class GetUsedBytesQuery(BaseRequestModel):
    """Query parameters for getting used bytes information."""

    folder_host: str = Field(description="Folder host")
    id: uuid.UUID = Field(description="Quota scope ID")


class GetFstabContentsQuery(BaseRequestModel):
    """Query parameters for getting fstab contents."""

    fstab_path: str | None = Field(default=None, description="Path to fstab file")
    agent_id: str | None = Field(default=None, description="Agent ID to query")


class MountHostReq(BaseRequestModel):
    """Request to mount a host filesystem."""

    fs_location: str = Field(description="Filesystem location to mount")
    name: str = Field(description="Name for the mount")
    fs_type: str = Field(default="nfs", description="Filesystem type")
    options: str | None = Field(default=None, description="Mount options")
    scaling_group: str | None = Field(default=None, description="Target scaling group")
    fstab_path: str | None = Field(default=None, description="Path to fstab file")
    edit_fstab: bool = Field(default=False, description="Whether to edit fstab file")


class UmountHostReq(BaseRequestModel):
    """Request to unmount a host filesystem."""

    name: str = Field(description="Name of the mount to remove")
    scaling_group: str | None = Field(default=None, description="Target scaling group")
    fstab_path: str | None = Field(default=None, description="Path to fstab file")
    edit_fstab: bool = Field(default=False, description="Whether to edit fstab file")


class ChangeVFolderOwnershipReq(BaseRequestModel):
    """Request to change virtual folder ownership."""

    vfolder: uuid.UUID = Field(description="VFolder ID")
    user_email: str = Field(description="Email of the new owner")
