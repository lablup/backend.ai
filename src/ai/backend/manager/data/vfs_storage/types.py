from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from ai.backend.common.data.storage.types import VFSStorageStatefulData


@dataclass
class VFSStorageListResult:
    """Search result with total count for VFS storages."""

    items: list[VFSStorageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class VFSStorageData:
    id: uuid.UUID
    name: str
    host: str
    base_path: Path

    @classmethod
    def from_stateful_data(cls, data: VFSStorageStatefulData) -> Self:
        return cls(
            id=data.id,
            name=data.name,
            host=data.host,
            base_path=data.base_path,
        )

    def to_stateful_data(self) -> VFSStorageStatefulData:
        return VFSStorageStatefulData(
            id=self.id,
            name=self.name,
            host=self.host,
            base_path=self.base_path,
        )
