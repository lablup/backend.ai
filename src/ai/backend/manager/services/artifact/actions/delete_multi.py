import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class DeleteArtifactsAction(ArtifactAction):
    artifact_ids: list[uuid.UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_artifacts"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteArtifactsActionResult:
    artifacts: list[ArtifactData]
