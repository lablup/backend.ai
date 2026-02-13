from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.vfs_storage.types import VFSStorageData
from ai.backend.manager.models.vfs_storage import VFSStorageRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.vfs_storage.actions.base import VFSStorageAction

if TYPE_CHECKING:
    from ai.backend.manager.models.artifact_storages import ArtifactStorageRow


@dataclass
class CreateVFSStorageAction(VFSStorageAction):
    creator: Creator[VFSStorageRow]
    meta_creator: Creator[ArtifactStorageRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateVFSStorageActionResult(BaseActionResult):
    result: VFSStorageData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
