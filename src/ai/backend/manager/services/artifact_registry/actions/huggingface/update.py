from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryModifierMeta
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class UpdateHuggingFaceRegistryAction(ArtifactRegistryAction):
    updater: Updater[HuggingFaceRegistryRow]
    meta: ArtifactRegistryModifierMeta

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_huggingface_registry"


@dataclass
class UpdateHuggingFaceRegistryActionResult(BaseActionResult):
    result: HuggingFaceRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.result.id)
