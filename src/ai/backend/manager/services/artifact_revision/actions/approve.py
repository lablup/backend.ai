from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact_revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class ApproveArtifactRevisionAction(ArtifactRevisionSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "approve_artifact_revision"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ApproveArtifactRevisionActionResult:
    result: ArtifactRevisionData
