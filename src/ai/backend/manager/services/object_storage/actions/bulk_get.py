from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.queriers import BulkObjectStorageQuerier
from ai.backend.manager.models.object_storage.row import ObjectStorageRow


@dataclass
class BulkGetObjectStoragesAction(
    PartialBulkGetEntityOpsAction[ObjectStorageRow, ObjectStorageData]
):
    """Read the object storages the caller named, answering for each id."""

    ids: Sequence[ObjectStorageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_object_storages"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkObjectStorageQuerier:
        return BulkObjectStorageQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
