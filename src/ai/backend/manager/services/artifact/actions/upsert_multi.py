from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class UpsertArtifactsAction(ArtifactAction):
    data: list[ArtifactDataWithRevisions]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "upsert_artifacts"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpsertArtifactsActionResult:
    result: list[ArtifactDataWithRevisions]
