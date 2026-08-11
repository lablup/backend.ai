from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.repositories.vfs_storage.queriers import VFSStorageQuerier


@dataclass
class GetVFSStorageAction(GetGlobalOpsAction[VFSStorageRow, VFSStorageData]):
    """Read one VFS storage registration by id.

    The name-keyed path is its own lookup action — a branch on which key the
    caller supplied belongs to the adapter, not inside a read."""

    storage_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_vfs_storage"

    @override
    def to_querier(self) -> VFSStorageQuerier:
        return VFSStorageQuerier(storage_id=self.storage_id)
