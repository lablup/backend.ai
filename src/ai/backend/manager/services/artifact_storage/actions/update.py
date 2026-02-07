from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact_storages.types import ArtifactStorageData
from ai.backend.manager.models.artifact_storages import ArtifactStorageRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact_storage.actions.base import ArtifactStorageAction


@dataclass
class UpdateArtifactStorageAction(ArtifactStorageAction):
    updater: Updater[ArtifactStorageRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateArtifactStorageActionResult(BaseActionResult):
    result: ArtifactStorageData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
