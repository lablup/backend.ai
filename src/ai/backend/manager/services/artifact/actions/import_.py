from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction
from ai.backend.manager.services.artifact.actions.types import ImportArtifactTarget


@dataclass
class ImportArtifactAction(ArtifactAction):
    target: ImportArtifactTarget

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.target.artifact_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "import"


@dataclass
class ImportArtifactActionResult(BaseActionResult):
    result: ArtifactData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
