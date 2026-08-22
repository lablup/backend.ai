from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact.actions.base import ArtifactSingleEntityAction


@dataclass
class GetArtifactRevisionsAction(ArtifactSingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_revisions"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class GetArtifactRevisionsActionResult:
    revisions: list[ArtifactRevisionData]
