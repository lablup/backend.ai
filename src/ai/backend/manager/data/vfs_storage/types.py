from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.common.data.entity.vfs_storage import VFSStorageID
from ai.backend.common.data.entity.types import EntityData, EntityID, EntityIdentifier


@dataclass
class VFSStorageListResult:
    """Search result with total count for VFS storages."""

    items: list[VFSStorageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class VFSStorageData(EntityData):
    id: VFSStorageID
    name: str
    host: str
    base_path: Path

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id
