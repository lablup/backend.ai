import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


# TODO: Make this a batch action.
@dataclass
class ImportArtifactBatchAction(ArtifactRevisionAction):
    artifact_revision_ids: list[uuid.UUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ImportArtifactBatchActionResult(BaseActionResult):
    result: list[ArtifactRevisionData]

    @override
    def entity_id(self) -> str | None:
        return None
