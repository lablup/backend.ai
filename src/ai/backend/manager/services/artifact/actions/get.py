from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.services.artifact.actions.base import (
    ArtifactSingleEntityAction,
)


@dataclass
class GetArtifactAction(ArtifactSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactActionResult:
    result: ArtifactData
