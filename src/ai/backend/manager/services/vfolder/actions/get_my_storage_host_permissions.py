from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.types import VFolderHostPermission
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import VFolderAction


@dataclass
class StorageHostPermissionEntry:
    """Single storage host with its granted permissions for a user."""

    host: str
    permissions: list[VFolderHostPermission]


@dataclass
class GetMyStorageHostPermissionsAction(VFolderAction):
    """Resolve the storage hosts and permissions accessible to the current user."""

    user_uuid: uuid.UUID
    domain_name: str

    @override
    def entity_id(self) -> str | None:
        return str(self.user_uuid)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetMyStorageHostPermissionsActionResult(BaseActionResult):
    user_uuid: uuid.UUID
    items: list[StorageHostPermissionEntry]

    @override
    def entity_id(self) -> str | None:
        return str(self.user_uuid)
