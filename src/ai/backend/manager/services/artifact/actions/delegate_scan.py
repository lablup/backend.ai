import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import (
    ArtifactDataWithRevisions,
    ArtifactRevisionReadme,
    ArtifactType,
    DelegateeTarget,
)
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class DelegateScanArtifactsAction(ArtifactAction):
    delegator_reservoir_id: Optional[uuid.UUID]
    artifact_type: Optional[ArtifactType]
    search: Optional[str]
    order: Optional[ModelSortKey]
    delegatee_target: Optional[DelegateeTarget]
    limit: Optional[int]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delegate_scan"


@dataclass
class DelegateScanArtifactsActionResult(BaseActionResult):
    result: list[ArtifactDataWithRevisions]
    source_registry_id: uuid.UUID
    source_registry_type: ArtifactRegistryType
    readme_data: dict[uuid.UUID, ArtifactRevisionReadme]

    @override
    def entity_id(self) -> Optional[str]:
        return None
