from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.models.artifact.updaters import ArtifactUpdater
from ai.backend.manager.services.artifact.actions.base import (
    ArtifactSingleEntityAction,
)


@dataclass
class UpdateArtifactAction(ArtifactSingleEntityAction):
    updater: ArtifactUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_artifact"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateArtifactActionResult:
    result: ArtifactData
