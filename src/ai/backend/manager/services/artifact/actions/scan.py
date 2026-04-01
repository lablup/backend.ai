import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.actions.action import BaseActionResult
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
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT_SCAN

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ScanArtifactsActionResult(BaseActionResult):
    result: list[ArtifactDataWithRevisions]

    @override
    def entity_id(self) -> str | None:
        return None
