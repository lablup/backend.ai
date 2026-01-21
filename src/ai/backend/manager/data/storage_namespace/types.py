from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class StorageNamespaceListResult:
    """Search result with total count for storage namespaces."""

    items: list[StorageNamespaceData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class StorageNamespaceData:
    id: uuid.UUID
    storage_id: uuid.UUID
    namespace: str
