from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.types import EntityData, EntityID, EntityIdentifier
from ai.backend.common.dto.manager.response import ObjectStorageResponse


@dataclass
class ObjectStorageListResult:
    """Search result with total count for Object storages."""

    items: list[ObjectStorageData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class ObjectStorageData(EntityData):
    id: ObjectStorageID
    name: str
    host: str
    access_key: str
    secret_key: str
    endpoint: str
    region: str | None

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.id

    def to_dto(self) -> ObjectStorageResponse:
        return ObjectStorageResponse(
            id=str(self.id),
            name=self.name,
            host=self.host,
            access_key=self.access_key,
            secret_key=self.secret_key,
            endpoint=self.endpoint,
            region=self.region or "",
        )
