from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage import ObjectStorageRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.object_storage.actions.base import ObjectStorageAction

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact_storages import ArtifactStorageRow


@dataclass
class CreateObjectStorageAction(ObjectStorageAction):
    creator: Creator[ObjectStorageRow]
    meta_creator: Creator[ArtifactStorageRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateObjectStorageActionResult(BaseActionResult):
    result: ObjectStorageData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
