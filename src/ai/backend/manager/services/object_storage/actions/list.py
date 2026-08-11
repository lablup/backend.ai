from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import OBJECT_STORAGE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.repositories.object_storage.searchers import ObjectStorageSearcher


@dataclass
class ListObjectStorageAction(SearchGlobalOpsAction[ObjectStorageRow, ObjectStorageData]):
    """Every registered object storage, unpaged."""

    searcher: ObjectStorageSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return OBJECT_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_object_storages"

    @override
    def to_searcher(self) -> ObjectStorageSearcher:
        return self.searcher
