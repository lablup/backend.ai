from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryCreatorMeta
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.models.huggingface_registry.creators import HuggingFaceRegistryCreator
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class CreateHuggingFaceRegistryAction(ArtifactRegistryAction):
    creator: HuggingFaceRegistryCreator
    meta: ArtifactRegistryCreatorMeta

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_hugging_face_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateHuggingFaceRegistryActionResult:
    result: HuggingFaceRegistryData
