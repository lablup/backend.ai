from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact.revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class GetArtifactRevisionAction(ArtifactRevisionSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_revision"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactRevisionActionResult:
    revision: ArtifactRevisionData
