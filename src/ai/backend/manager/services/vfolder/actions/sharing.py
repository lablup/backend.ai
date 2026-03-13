from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.vfolder import VFolderOperationStatus, VFolderPermission

from .base import VFolderAction


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
    vfolder_uuid: uuid.UUID
    resource_policy: Mapping[str, Any]
    permission: VFolderPermission
    emails: list[str] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class ShareVFolderActionResult(BaseActionResult):
    shared_emails: list[str] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class UnshareVFolderAction(VFolderAction):
    """Revoke direct sharing permissions from users."""

    user_uuid: uuid.UUID
    vfolder_uuid: uuid.UUID
    resource_policy: Mapping[str, Any]
    emails: list[str] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_uuid)


@dataclass
class UnshareVFolderActionResult(BaseActionResult):
    unshared_emails: list[str] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ListSharedVFoldersAction(VFolderAction):
    """List all shared vfolder permissions, optionally filtered by vfolder ID."""

    vfolder_id: uuid.UUID | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id) if self.vfolder_id else None


@dataclass
class ListSharedVFoldersActionResult(BaseActionResult):
    shared: list[VFolderSharedInfo] = field(default_factory=list)

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class UpdateVFolderSharingStatusAction(VFolderAction):
    """Batch update or delete sharing permissions."""

    vfolder_id: uuid.UUID = field(default_factory=uuid.uuid4)
    to_delete: list[uuid.UUID] = field(default_factory=list)
    to_update: list[tuple[uuid.UUID, VFolderPermission]] = field(default_factory=list)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.vfolder_id)


@dataclass
class UpdateVFolderSharingStatusActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None
