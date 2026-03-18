import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import (
    ArtifactRevisionData,
    ArtifactType,
    DelegateeTarget,
)
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


# TODO: Make this a batch action.
@dataclass
class DelegateImportArtifactRevisionBatchAction(ArtifactRevisionAction):
    delegator_reservoir_id: uuid.UUID | None
    artifact_type: ArtifactType | None
    delegatee_target: DelegateeTarget | None
    artifact_revision_ids: list[uuid.UUID]
    force: bool

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class DelegateImportArtifactRevisionBatchActionResult(BaseActionResult):
    result: list[ArtifactRevisionData]
    task_ids: list[uuid.UUID | None]

    @override
    def entity_id(self) -> str | None:
        return None
