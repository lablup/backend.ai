import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact_registries.types import (
    ArtifactRegistryData,
)
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.reservoir.types import ReservoirRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetArtifactRegistryAction(ArtifactRegistryAction):
    registry_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.registry_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_artifact_registry"


@dataclass
class GetArtifactRegistryActionResult(BaseActionResult):
    result: HuggingFaceRegistryData | ReservoirRegistryData
    common: ArtifactRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return None
