from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.vfs_storage import VFSStorageID
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class VFSStoragePurger(EntityPurger[VFSStorageRow, VFSStorageData]):
    """Purger for removing a VFS storage registration."""

    storage_id: VFSStorageID

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def pk_value(self) -> VFSStorageID:
        return self.storage_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.storage_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return row.to_dataclass()
