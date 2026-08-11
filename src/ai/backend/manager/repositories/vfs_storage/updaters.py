"""DataUpdater implementations for the VFS storage repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.models.vfs_storage.row import VFSStorageRow
from ai.backend.manager.types import OptionalState


@dataclass
class VFSStorageUpdater(DataUpdater[VFSStorageRow, VFSStorageData]):
    storage_id: uuid.UUID
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    host: OptionalState[str] = field(default_factory=OptionalState.nop)
    base_path: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def pk_value(self) -> uuid.UUID:
        return self.storage_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.host.update_dict(to_update, "host")
        self.base_path.update_dict(to_update, "base_path")
        return to_update

    @override
    def to_data(self, row: VFSStorageRow) -> VFSStorageData:
        return row.to_dataclass()
