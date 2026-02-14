"""
Response DTOs for VFolder API endpoints.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.dto.manager.field import (
    VFolderItemField,
    VFolderOperationStatusField,
    VFolderOwnershipTypeField,
    VFolderPermissionField,
)
from ai.backend.common.types import VFolderUsageMode

__all__ = (
    # DTOs (data transfer objects)
    "CompactVFolderInfoDTO",
    "MountResultDTO",
    "VFolderCloneInfoDTO",
    "VFolderCreatedDTO",
    "VFolderInfoDTO",
    "VFolderInvitationDTO",
    "VFolderSharedInfoDTO",
    "VolumeInfoDTO",
    # Response wrappers - CRUD
    "VFolderCloneResponse",
    "VFolderCreateResponse",
    "VFolderGetIDResponse",
    "VFolderGetInfoResponse",
    "VFolderListResponse",
    # Response wrappers - File Operations
    "CreateDownloadSessionResponse",
    "CreateUploadSessionResponse",
    "DeleteFilesAsyncResponse",
    "ListFilesResponse",
    "MkdirResponse",
    # Response wrappers - Sharing/Invitations
    "InviteVFolderResponse",
    "ListInvitationsResponse",
    "ListSentInvitationsResponse",
    "ListSharedVFoldersResponse",
    "ShareVFolderResponse",
    "UnshareVFolderResponse",
    # Response wrappers - Admin
    "GetFstabContentsResponse",
    "GetQuotaResponse",
    "GetUsageResponse",
    "GetUsedBytesResponse",
    "ListAllHostsResponse",
    "ListAllowedTypesResponse",
    "ListHostsResponse",
    "ListMountsResponse",
    "MessageResponse",
    "UpdateQuotaResponse",
)


# ============================================================
# DTOs (data transfer objects)
# ============================================================


class VFolderCreatedDTO(BaseModel):
    """DTO for a newly created vfolder."""

    id: str = Field(description="VFolder ID (hex UUID)")
    name: str = Field(description="VFolder name")
    quota_scope_id: str = Field(description="Quota scope ID")
    host: str = Field(description="Host name")
    usage_mode: VFolderUsageMode = Field(description="Usage mode")
    permission: VFolderPermissionField = Field(description="Permission level")
    max_size: int = Field(description="Maximum size in bytes")
    creator: str = Field(description="Creator email")
    ownership_type: VFolderOwnershipTypeField = Field(description="Ownership type")
    user: str | None = Field(default=None, description="Owner user UUID")
    group: str | None = Field(default=None, description="Owner group UUID")
    cloneable: bool = Field(description="Whether the vfolder is cloneable")
    status: VFolderOperationStatusField = Field(description="Operation status")
    unmanaged_path: str | None = Field(default=None, description="Unmanaged path if any")


class VFolderInfoDTO(BaseModel):
    """DTO for detailed vfolder information."""

    name: str = Field(description="VFolder name")
    id: str = Field(description="VFolder ID (hex UUID)")
    quota_scope_id: str = Field(description="Quota scope ID")
    host: str = Field(description="Host name")
    status: VFolderOperationStatusField = Field(description="Operation status")
    num_files: int = Field(description="Number of files")
    used_bytes: int = Field(description="Used bytes")
    created_at: str = Field(description="Creation timestamp")
    last_used: str | None = Field(default=None, description="Last used timestamp")
    user: str | None = Field(default=None, description="Owner user UUID")
    group: str | None = Field(default=None, description="Owner group UUID")
    type: str = Field(description="VFolder type (user or group)")
    is_owner: bool = Field(description="Whether current user is the owner")
    permission: VFolderPermissionField = Field(description="Permission level")
    usage_mode: VFolderUsageMode = Field(description="Usage mode")
    cloneable: bool = Field(description="Whether the vfolder is cloneable")


class CompactVFolderInfoDTO(BaseModel):
    """DTO for compact vfolder information (ID + name only)."""

    id: uuid.UUID = Field(description="VFolder ID")
    name: str = Field(description="VFolder name")


class VFolderInvitationDTO(BaseModel):
    """DTO for vfolder invitation data."""

    id: str = Field(description="Invitation ID")
    inviter: str = Field(description="Inviter email")
    invitee: str = Field(description="Invitee email")
    perm: VFolderPermissionField = Field(description="Permission level")
    state: str = Field(description="Invitation state")
    created_at: str = Field(description="Creation timestamp")
    modified_at: str | None = Field(default=None, description="Last modification timestamp")
    vfolder_id: str = Field(description="VFolder ID")
    vfolder_name: str = Field(description="VFolder name")


class VFolderSharedInfoDTO(BaseModel):
    """DTO for shared vfolder information."""

    vfolder_id: str = Field(description="VFolder ID")
    vfolder_name: str = Field(description="VFolder name")
    status: str = Field(description="VFolder status")
    owner: str = Field(description="Owner UUID")
    type: str = Field(description="VFolder type (user or project)")
    shared_to: dict[str, str] = Field(description="Shared user info with 'uuid' and 'email' keys")
    perm: VFolderPermissionField = Field(description="Permission level")


class VFolderCloneInfoDTO(BaseModel):
    """DTO for cloned vfolder information."""

    id: str = Field(description="Cloned VFolder ID (hex UUID)")
    name: str = Field(description="Cloned VFolder name")
    host: str = Field(description="Host name")
    usage_mode: VFolderUsageMode = Field(description="Usage mode")
    permission: VFolderPermissionField = Field(description="Permission level")
    creator: str = Field(description="Creator email")
    ownership_type: VFolderOwnershipTypeField = Field(description="Ownership type")
    user: str | None = Field(default=None, description="Owner user UUID")
    group: str | None = Field(default=None, description="Owner group UUID")
    cloneable: bool = Field(description="Whether the cloned vfolder is cloneable")
    bgtask_id: str = Field(description="Background task ID for the clone operation")


class VolumeInfoDTO(BaseModel):
    """DTO for volume host information."""

    backend: str = Field(description="Storage backend type")
    capabilities: list[str] = Field(description="Volume capabilities")
    usage: dict[str, Any] | None = Field(default=None, description="Volume usage info")
    sftp_scaling_groups: list[str] | None = Field(default=None, description="SFTP scaling groups")


class MountResultDTO(BaseModel):
    """DTO for mount/umount operation result per node."""

    success: bool = Field(description="Whether the operation succeeded")
    mounts: list[Any] | None = Field(default=None, description="Mount entries")
    message: str = Field(default="", description="Result message")


# ============================================================
# Response wrappers - CRUD
# ============================================================


class VFolderCreateResponse(BaseResponseModel):
    """Response for vfolder creation."""

    item: VFolderItemField


class VFolderListResponse(BaseResponseModel):
    """Response for listing vfolders."""

    items: list[VFolderItemField] = Field(default_factory=list)


class VFolderGetInfoResponse(BaseResponseModel):
    """Response for getting vfolder info."""

    item: VFolderInfoDTO = Field(description="VFolder information")


class VFolderGetIDResponse(BaseResponseModel):
    """Response for getting vfolder ID by name."""

    item: CompactVFolderInfoDTO = Field(description="Compact vfolder info")


class VFolderCloneResponse(BaseResponseModel):
    """Response for cloning a vfolder."""

    item: VFolderCloneInfoDTO = Field(description="Cloned vfolder info")


# ============================================================
# Response wrappers - File Operations
# ============================================================


class MkdirResponse(BaseResponseModel):
    """Response for mkdir operation."""

    results: list[Any] = Field(description="Results of directory creation")


class CreateDownloadSessionResponse(BaseResponseModel):
    """Response for creating a download session."""

    token: str = Field(description="Download session token")
    url: str = Field(description="Download URL")


class CreateUploadSessionResponse(BaseResponseModel):
    """Response for creating an upload session."""

    token: str = Field(description="Upload session token")
    url: str = Field(description="Upload URL")


class ListFilesResponse(BaseResponseModel):
    """Response for listing files in a vfolder."""

    items: list[Any] = Field(description="List of file entries")


class DeleteFilesAsyncResponse(BaseResponseModel):
    """Response for asynchronous file deletion operation."""

    bgtask_id: TaskID = Field(
        description=(
            "Unique identifier for the background file deletion task. "
            "Use this ID to subscribe to task progress updates via GraphQL subscriptions "
            "or to check the current status of the deletion operation."
        ),
    )


# ============================================================
# Response wrappers - Sharing/Invitations
# ============================================================


class InviteVFolderResponse(BaseResponseModel):
    """Response for inviting users to a vfolder."""

    invited_ids: list[str] = Field(description="List of invited user UUIDs")


class ListInvitationsResponse(BaseResponseModel):
    """Response for listing received invitations."""

    invitations: list[VFolderInvitationDTO] = Field(description="List of invitations")


class ListSentInvitationsResponse(BaseResponseModel):
    """Response for listing sent invitations."""

    invitations: list[VFolderInvitationDTO] = Field(description="List of sent invitations")


class ShareVFolderResponse(BaseResponseModel):
    """Response for sharing a vfolder."""

    shared_emails: list[str] = Field(description="List of emails the vfolder was shared with")


class UnshareVFolderResponse(BaseResponseModel):
    """Response for unsharing a vfolder."""

    unshared_emails: list[str] = Field(description="List of emails the vfolder was unshared from")


class ListSharedVFoldersResponse(BaseResponseModel):
    """Response for listing shared vfolders."""

    shared: list[VFolderSharedInfoDTO] = Field(description="List of shared vfolder info")


# ============================================================
# Response wrappers - Admin
# ============================================================


class ListHostsResponse(BaseResponseModel):
    """Response for listing vfolder hosts."""

    default: str | None = Field(description="Default folder host")
    allowed: list[str] = Field(description="Allowed folder hosts")
    volume_info: dict[str, VolumeInfoDTO] = Field(
        default_factory=dict, description="Volume info per host"
    )


class ListAllHostsResponse(BaseResponseModel):
    """Response for listing all vfolder hosts (superadmin)."""

    default: str | None = Field(description="Default folder host")
    allowed: list[str] = Field(description="Allowed folder hosts")


class ListAllowedTypesResponse(BaseResponseModel):
    """Response for listing allowed vfolder types."""

    allowed_types: list[str] = Field(description="Allowed vfolder types")


class GetQuotaResponse(BaseResponseModel):
    """Response for getting quota information."""

    data: dict[str, Any] = Field(description="Quota data from storage proxy")


class UpdateQuotaResponse(BaseResponseModel):
    """Response for updating quota."""

    size_bytes: int = Field(description="Updated quota size in bytes")


class GetUsageResponse(BaseResponseModel):
    """Response for getting usage information."""

    data: dict[str, Any] = Field(description="Usage data from storage proxy")


class GetUsedBytesResponse(BaseResponseModel):
    """Response for getting used bytes information."""

    data: dict[str, Any] = Field(description="Used bytes data from storage proxy")


class GetFstabContentsResponse(BaseResponseModel):
    """Response for getting fstab contents."""

    content: str = Field(description="fstab file contents")
    node: str = Field(description="Node type (agent or manager)")
    node_id: str = Field(description="Node identifier")


class ListMountsResponse(BaseResponseModel):
    """Response for listing mounted filesystems."""

    manager: MountResultDTO = Field(description="Manager mount status")
    storage_proxy: MountResultDTO | None = Field(
        default=None, description="Storage proxy mount status"
    )
    agents: dict[str, MountResultDTO] = Field(
        default_factory=dict, description="Agent mount status per agent ID"
    )


class MessageResponse(BaseResponseModel):
    """Generic message response for operations like leave, update invitation, etc."""

    msg: str = Field(description="Result message")
