from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import OBJECT_STORAGE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeGlobalOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.purgers import ObjectStoragePurger
from ai.backend.manager.models.object_storage.row import ObjectStorageRow


@dataclass
class PurgeObjectStorageAction(PurgeGlobalOpsAction[ObjectStorageRow, ObjectStorageData]):
    """Remove an object storage registration.

    Purge-shaped: the table carries no lifecycle column, so removing one has
    always been the row leaving the table."""

    storage_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return OBJECT_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_object_storage"

    @override
    def to_purger(self) -> ObjectStoragePurger:
        return ObjectStoragePurger(storage_id=self.storage_id)
