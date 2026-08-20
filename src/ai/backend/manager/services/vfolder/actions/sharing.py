from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.vfolder import VFolderOperationStatus, VFolderPermission

from .base import VFolderAction, VFolderGlobalAction


@dataclass
class VFolderSharedInfo:
    """Domain type for shared vfolder permission info."""

    vfolder_id: uuid.UUID
    vfolder_name: str
    status: VFolderOperationStatus
    owner: str
    folder_type: str  # "project" or "user"
    shared_user_uuid: uuid.UUID
    shared_user_email: str
    permission: VFolderPermission


@dataclass
class ShareVFolderAction(VFolderAction):
    """Share a group vfolder with users by granting permissions directly."""

    user_uuid: uuid.UUID
    resource_policy: Mapping[str, Any]
    permission: VFolderPermission
    emails: list[str] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "share_vfolder"


@dataclass
class ShareVFolderActionResult:
    shared_emails: list[str] = field(default_factory=list)


@dataclass
class UnshareVFolderAction(VFolderAction):
    """Revoke direct sharing permissions from users."""

    user_uuid: uuid.UUID
    resource_policy: Mapping[str, Any]
    emails: list[str] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "unshare_vfolder"


@dataclass
class UnshareVFolderActionResult:
    unshared_emails: list[str] = field(default_factory=list)


@dataclass
class ListSharedVFoldersAction(VFolderAction):
    """List the sharing permissions granted on one vfolder."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_shared_vfolders"


@dataclass
class ListSharedVFoldersActionResult:
    shared: list[VFolderSharedInfo] = field(default_factory=list)


@dataclass
class UpdateVFolderSharingStatusAction(VFolderAction):
    """Batch update or delete sharing permissions."""

    to_delete: list[uuid.UUID] = field(default_factory=list)
    to_update: list[tuple[uuid.UUID, VFolderPermission]] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_vfolder_sharing_status"


@dataclass
class UpdateVFolderSharingStatusActionResult:
    pass


@dataclass
class PublicListSharedVFoldersAction(VFolderGlobalAction):
    """List the sharing permissions granted across every vfolder.

    Read-only and open to any authenticated caller, as the legacy route was.
    """

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_list_shared_vfolders"


@dataclass
class PublicListSharedVFoldersActionResult:
    shared: list[VFolderSharedInfo] = field(default_factory=list)
