from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryModifierMeta
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
)


@dataclass
class UpdateHuggingFaceRegistryAction(ArtifactRegistrySingleEntityAction):
    updater: Updater[HuggingFaceRegistryRow]
    meta: ArtifactRegistryModifierMeta

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_hugging_face_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateHuggingFaceRegistryActionResult:
    result: HuggingFaceRegistryData
