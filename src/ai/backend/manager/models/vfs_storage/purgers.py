from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow


@dataclass
class VFSStoragePurger(GlobalEntityPurger[VFSStorageRow, VFSStorageData]):
    """Purger for removing a VFS storage registration."""

    storage_id: uuid.UUID

    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.storage_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return row.to_dataclass()
