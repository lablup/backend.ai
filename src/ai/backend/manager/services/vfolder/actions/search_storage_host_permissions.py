from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE
from ai.backend.common.types import VFolderHostPermission
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.vfolder.actions.base import (
    VFolderScopeAction,
    VFolderScopeActionResult,
)


@dataclass
class StorageHostPermissionEntry:
    """Single storage host with its granted permissions for a user."""

    host: str
    permissions: list[VFolderHostPermission]


@dataclass
class SearchStorageHostPermissionsAction(VFolderScopeAction):
    """Resolve the storage hosts and permissions a user holds."""

    user_uuid: uuid.UUID
    domain_name: str

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_uuid),)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_storage_host_permissions"


@dataclass
class SearchStorageHostPermissionsActionResult(VFolderScopeActionResult):
    user_uuid: uuid.UUID
    items: list[StorageHostPermissionEntry]
