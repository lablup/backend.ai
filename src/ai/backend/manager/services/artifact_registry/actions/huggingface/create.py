from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryCreatorMeta
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class CreateHuggingFaceRegistryAction(ArtifactRegistryAction):
    creator: Creator[HuggingFaceRegistryRow]
    meta: ArtifactRegistryCreatorMeta

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_huggingface_registry"


@dataclass
class CreateHuggingFaceRegistryActionResult(BaseActionResult):
    result: HuggingFaceRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
