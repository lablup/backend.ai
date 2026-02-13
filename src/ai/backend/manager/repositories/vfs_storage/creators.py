"""CreatorSpec implementations for VFS storage domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class VFSStorageCreatorSpec(CreatorSpec[VFSStorageRow]):
    """CreatorSpec for VFS storage creation."""

    host: str
    base_path: str

    @override
    def build_row(self) -> VFSStorageRow:
        return VFSStorageRow(
            host=self.host,
            base_path=self.base_path,
        )
