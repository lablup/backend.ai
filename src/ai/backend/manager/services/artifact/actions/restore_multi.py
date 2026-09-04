import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class RestoreArtifactsAction(ArtifactAction):
    artifact_ids: list[uuid.UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_artifacts"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class RestoreArtifactsActionResult:
    artifacts: list[ArtifactData]
    missing: list[ArtifactID]
