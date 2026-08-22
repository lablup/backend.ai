from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.models.vfs_storage.updaters import VFSStorageUpdater


@dataclass
class UpdateVFSStorageAction(UpdateSingleEntityOpsAction[VFSStorageRow, VFSStorageData]):
    """Retune one VFS storage registration."""

    updater: VFSStorageUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_vfs_storage"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.storage_id

    @override
    def to_updater(self) -> VFSStorageUpdater:
        return self.updater
