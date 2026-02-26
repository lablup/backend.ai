from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.data.storage.types import ArtifactStorageData


@dataclass
class VFSStorageListResult:
    """Search result with total count for VFS storages."""

    items: list[VFSStorageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass(frozen=True)
class VFSStorageData(ArtifactStorageData):
    host: str
    base_path: Path
