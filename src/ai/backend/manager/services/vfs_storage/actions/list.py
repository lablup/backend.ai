from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfs_storage import VFSStorageEntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass(frozen=True)
class ListVFSStorageAction(GlobalSearcherOpsAction[VFSStorageRow, VFSStorageData]):
    """Every registered VFS storage, unpaged."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFSStorageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_vfs_storages"
