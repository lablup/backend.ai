from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.object_storage import ObjectStorageID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.purgers import ObjectStoragePurger
from ai.backend.manager.models.object_storage.row import ObjectStorageRow


@dataclass(frozen=True)
class PartialBulkPurgeObjectStoragesAction(
    PartialBulkPurgeEntityOpsAction[ObjectStorageRow, ObjectStorageData]
):
    """Remove the named object storage registrations, answering for each one."""

    ids: Sequence[ObjectStorageID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_object_storages"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, ObjectStoragePurger]:
        return {storage_id: ObjectStoragePurger(storage_id=storage_id) for storage_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[storage_id for storage_id in self.ids if storage_id in allowed])
