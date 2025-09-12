import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetArtifactRegistryMetaAction(ArtifactRegistryAction):
    registry_id: Optional[uuid.UUID] = None
    registry_name: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.registry_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_meta"


@dataclass
class GetArtifactRegistryMetaActionResult(BaseActionResult):
    result: ArtifactRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
