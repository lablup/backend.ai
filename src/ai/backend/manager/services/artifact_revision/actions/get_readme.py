import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionReadme
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


@dataclass
class GetArtifactRevisionReadmeAction(ArtifactRevisionAction):
    artifact_revision_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.artifact_revision_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactRevisionReadmeActionResult(BaseActionResult):
    readme_data: ArtifactRevisionReadme

    @override
    def entity_id(self) -> str | None:
        return None
