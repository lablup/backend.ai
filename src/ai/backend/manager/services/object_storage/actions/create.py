from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.object_storage import OBJECT_STORAGE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.creators import ObjectStorageCreator
from ai.backend.manager.models.object_storage.row import ObjectStorageRow


@dataclass
class CreateObjectStorageAction(CreateGlobalOpsAction[ObjectStorageRow, ObjectStorageData]):
    """Register an object storage."""

    creator: ObjectStorageCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return OBJECT_STORAGE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_object_storage"

    @override
    def to_creator(self) -> ObjectStorageCreator:
        return self.creator
