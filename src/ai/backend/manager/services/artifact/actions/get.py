import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class GetArtifactAction(ArtifactAction):
    artifact_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.artifact_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get"


@dataclass
class GetArtifactActionResult(BaseActionResult):
    result: ArtifactData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
