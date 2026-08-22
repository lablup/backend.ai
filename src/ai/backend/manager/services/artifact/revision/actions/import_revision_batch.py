import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact.revision.actions.base import ArtifactRevisionAction


# TODO: Make this a batch action.
@dataclass
class ImportArtifactBatchAction(ArtifactRevisionAction):
    artifact_revision_ids: list[uuid.UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "import_artifact_batch"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ImportArtifactBatchActionResult:
    result: list[ArtifactRevisionData]
