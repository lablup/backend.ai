from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.repositories.object_storage.queriers import ObjectStorageQuerier


@dataclass
class GetObjectStorageAction(GetSingleEntityOpsAction[ObjectStorageRow, ObjectStorageData]):
    """Read one object storage registration."""

    storage_id: ObjectStorageID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_object_storage"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.storage_id

    @override
    def to_querier(self) -> ObjectStorageQuerier:
        return ObjectStorageQuerier(storage_id=self.storage_id)
