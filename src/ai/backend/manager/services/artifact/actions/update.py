from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class UpdateArtifactAction(ArtifactAction):
    updater: Updater[ArtifactRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateArtifactActionResult(BaseActionResult):
    result: ArtifactData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
