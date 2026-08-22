from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage.purgers import VFSStoragePurger
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class PurgeVFSStorageAction(PurgeEntityOpsAction[VFSStorageRow, VFSStorageData]):
    """Remove a VFS storage registration.

    Purge-shaped: the table carries no lifecycle column."""

    storage_id: uuid.UUID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_vfs_storage"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> VFSStoragePurger:
        return VFSStoragePurger(storage_id=VFSStorageID(self.storage_id))
