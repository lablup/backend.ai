import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactRevisionData
from ai.backend.manager.services.artifact_revision.actions.base import (
    ArtifactRevisionSingleEntityAction,
)


@dataclass
class ImportArtifactRevisionAction(ArtifactRevisionSingleEntityAction):
    vfolder_id: uuid.UUID | None = None
    storage_prefix: str | None = None
    force: bool = False

    @override
    @classmethod
    def action_name(cls) -> str:
        return "import_artifact_revision"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ImportArtifactRevisionActionResult:
    result: ArtifactRevisionData
    task_id: uuid.UUID | None
