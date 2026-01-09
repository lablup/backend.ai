from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path


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
