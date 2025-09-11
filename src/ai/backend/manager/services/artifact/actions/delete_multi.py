import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class DeleteArtifactsAction(ArtifactAction):
    artifact_ids: list[uuid.UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_multi"


@dataclass
class DeleteArtifactsActionResult(BaseActionResult):
    artifacts: list[ArtifactData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
