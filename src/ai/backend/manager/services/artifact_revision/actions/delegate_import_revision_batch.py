import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import (
    ArtifactRevisionData,
    ArtifactType,
    DelegateeTarget,
)
from ai.backend.manager.services.artifact_revision.actions.base import ArtifactRevisionAction


# TODO: Make this a batch action.
@dataclass
class DelegateImportArtifactRevisionBatchAction(ArtifactRevisionAction):
    delegator_reservoir_id: Optional[uuid.UUID]
    artifact_type: Optional[ArtifactType]
    delegatee_target: Optional[DelegateeTarget]
    artifact_revision_ids: list[uuid.UUID]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delegate_import_batch"


@dataclass
class DelegateImportArtifactRevisionBatchActionResult(BaseActionResult):
    result: list[ArtifactRevisionData]
    task_ids: list[Optional[uuid.UUID]]

    @override
    def entity_id(self) -> Optional[str]:
        return None
