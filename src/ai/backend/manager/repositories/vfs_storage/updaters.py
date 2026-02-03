"""UpdaterSpec implementations for VFS storage repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState


@dataclass
class VFSStorageUpdaterSpec(UpdaterSpec[VFSStorageRow]):
    """UpdaterSpec for VFS storage updates."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    host: OptionalState[str] = field(default_factory=OptionalState.nop)
    base_path: OptionalState[str] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[VFSStorageRow]:
        return VFSStorageRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.host.update_dict(to_update, "host")
        self.base_path.update_dict(to_update, "base_path")
        return to_update
