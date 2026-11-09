from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.purgers import VFSStoragePurger
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass(frozen=True)
class PartialBulkPurgeVFSStoragesAction(
    PartialBulkPurgeEntityOpsAction[VFSStorageRow, VFSStorageData]
):
    """Remove the named VFS storage registrations, answering for each one."""

    ids: Sequence[VFSStorageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_vfs_storages"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, VFSStoragePurger]:
        return {storage_id: VFSStoragePurger(storage_id=storage_id) for storage_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[storage_id for storage_id in self.ids if storage_id in allowed])
