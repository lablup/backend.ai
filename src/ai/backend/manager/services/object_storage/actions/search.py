from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import ObjectStorageEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow


@dataclass(frozen=True)
class SearchObjectStoragesAction(GlobalSearcherOpsAction[ObjectStorageRow, ObjectStorageData]):
    """Page through the registered object storages."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ObjectStorageEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_object_storages"
