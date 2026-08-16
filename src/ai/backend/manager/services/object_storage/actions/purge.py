from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import OBJECT_STORAGE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.object_storage import ObjectStorageID
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.purgers import ObjectStoragePurger
from ai.backend.manager.models.object_storage.row import ObjectStorageRow


@dataclass
class PurgeObjectStorageAction(PurgeEntityOpsAction[ObjectStorageRow, ObjectStorageData]):
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
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> ObjectStoragePurger:
        return ObjectStoragePurger(storage_id=ObjectStorageID(self.storage_id))
