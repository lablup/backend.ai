from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.vfs_storage.searchers import VFSStorageSearcher


@dataclass
class ListVFSStorageAction(SearchGlobalOpsAction[VFSStorageRow, VFSStorageData]):
    """Every registered VFS storage, unpaged."""

    searcher: VFSStorageSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_vfs_storages"

    @override
    def to_searcher(self) -> VFSStorageSearcher:
        return self.searcher
