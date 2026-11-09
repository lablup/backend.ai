from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.vfs_storage.updaters import VFSStorageUpdater


@dataclass(frozen=True)
class PartialBulkUpdateVFSStoragesAction(UpdatePartialBulkOpsAction[VFSStorageRow, VFSStorageData]):
    """Retune the named VFS storage registrations, answering for each one."""

    updaters: Sequence[VFSStorageUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_vfs_storages"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.storage_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, VFSStorageUpdater]:
        return {updater.storage_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.storage_id in allowed]
        )
