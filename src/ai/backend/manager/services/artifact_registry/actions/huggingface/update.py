from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
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
    def entity_id(self) -> str | None:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateHuggingFaceRegistryActionResult(BaseActionResult):
    result: HuggingFaceRegistryData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
