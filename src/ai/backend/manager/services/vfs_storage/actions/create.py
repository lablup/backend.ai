from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.creators import VFSStorageCreator
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class CreateVFSStorageAction(CreateGlobalOpsAction[VFSStorageRow, VFSStorageData]):
    """Register a VFS storage."""

    creator: VFSStorageCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_vfs_storage"

    @override
    def to_creator(self) -> VFSStorageCreator:
        return self.creator
