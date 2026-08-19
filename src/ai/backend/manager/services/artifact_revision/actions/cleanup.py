from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact_revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class CleanupArtifactRevisionAction(ArtifactRevisionSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "cleanup_artifact_revision"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class CleanupArtifactRevisionActionResult:
    result: ArtifactRevisionData
