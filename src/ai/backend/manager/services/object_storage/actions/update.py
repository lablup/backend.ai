from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.object_storage.types import ObjectStorageData
from ai.backend.manager.models.object_storage.row import ObjectStorageRow
from ai.backend.manager.models.object_storage.updaters import ObjectStorageUpdater


@dataclass
class UpdateObjectStorageAction(UpdateSingleEntityOpsAction[ObjectStorageRow, ObjectStorageData]):
    """Retune one object storage registration."""

    updater: ObjectStorageUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_object_storage"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.storage_id

    @override
    def to_updater(self) -> ObjectStorageUpdater:
        return self.updater
