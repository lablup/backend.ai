"""CreatorSpec implementations for VFS storage domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typing_extensions import override

from ai.backend.manager.repositories.base import CreatorSpec

if TYPE_CHECKING:
    from ai.backend.manager.models.vfs_storage import VFSStorageRow


@dataclass
class VFSStorageCreatorSpec(CreatorSpec["VFSStorageRow"]):
    """CreatorSpec for VFS storage creation."""

    name: str
    host: str
    base_path: str

    @override
    def build_row(self) -> VFSStorageRow:
        from ai.backend.manager.models.vfs_storage import VFSStorageRow

        return VFSStorageRow(
            name=self.name,
            host=self.host,
            base_path=self.base_path,
        )
