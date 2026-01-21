from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class UpdateArtifactAction(ArtifactAction):
    updater: Updater[ArtifactRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update"


@dataclass
class UpdateArtifactActionResult(BaseActionResult):
    result: ArtifactData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
