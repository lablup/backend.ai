import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions, ArtifactType
from ai.backend.manager.services.artifact.actions.base import ArtifactAction


@dataclass
class DelegateScanArtifactsAction(ArtifactAction):
    artifact_type: Optional[ArtifactType]
    registry_name: Optional[uuid.UUID]
    registry_id: Optional[uuid.UUID]
    limit: Optional[int]
    order: Optional[ModelSortKey]
    search: Optional[str]

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

    @override
    def entity_id(self) -> Optional[str]:
        return None
