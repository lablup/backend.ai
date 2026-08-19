import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisions,
    ArtifactRevisionReadme,
    ArtifactType,
    DelegateeTarget,
)
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class DelegateScanArtifactsAction(ArtifactAction):
    delegator_reservoir_id: uuid.UUID | None
    artifact_type: ArtifactType | None
    search: str | None
    order: ModelSortKey | None
    delegatee_target: DelegateeTarget | None
    limit: int | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delegate_scan_artifacts"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class DelegateScanArtifactsActionResult:
    result: list[ArtifactDataWithRevisions]
    source_registry_id: uuid.UUID
    source_registry_type: ArtifactRegistryType
    readme_data: dict[uuid.UUID, ArtifactRevisionReadme]
