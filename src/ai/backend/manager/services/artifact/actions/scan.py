import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions, ArtifactType
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class ScanArtifactsAction(ArtifactAction):
    artifact_type: ArtifactType | None
    registry_id: uuid.UUID | None
    limit: int | None
    order: ModelSortKey | None
    search: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scan_artifacts"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ScanArtifactsActionResult:
    result: list[ArtifactDataWithRevisions]
