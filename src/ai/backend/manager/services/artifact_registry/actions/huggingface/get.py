import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetHuggingFaceRegistryAction(ArtifactRegistryAction):
    registry_id: uuid.UUID

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.registry_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_huggingface_registry"


@dataclass
class GetHuggingFaceRegistryActionResult(BaseActionResult):
    result: HuggingFaceRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
