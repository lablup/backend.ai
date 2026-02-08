import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class RestoreArtifactsAction(ArtifactAction):
    artifact_ids: list[uuid.UUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class RestoreArtifactsActionResult(BaseActionResult):
    artifacts: list[ArtifactData]

    @override
    def entity_id(self) -> str | None:
        return None
