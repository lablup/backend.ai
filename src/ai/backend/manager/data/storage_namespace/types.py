from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.storage_namespace import StorageNamespaceID
from ai.backend.common.data.entity.types import EntityData, EntityID


@dataclass
class StorageNamespaceListResult:
    """Search result with total count for storage namespaces."""

    items: list[StorageNamespaceData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class StorageNamespaceData(EntityData):
    id: StorageNamespaceID
    storage_id: uuid.UUID
    namespace: str

    @override
    def entity_id(self) -> EntityID:
        return self.id
