from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.storage_backend_type import StorageBackendTypeID
from ai.backend.common.data.entity.types import EntityData, EntityIdentifier
from ai.backend.common.data.storage.types import (
    StorageBackendCapabilities,
    StorageBackendType,
)


@dataclass(frozen=True)
class StorageBackendTypeData(EntityData):
    id: StorageBackendTypeID
    name: StorageBackendType
    capabilities: StorageBackendCapabilities
    created_at: datetime
    updated_at: datetime

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id
