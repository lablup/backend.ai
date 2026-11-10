from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistryScopeAction,
)


@dataclass
class ListHuggingFaceRegistryAction(ArtifactRegistryScopeAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "list_hugging_face_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ListHuggingFaceRegistryActionResult:
    data: list[HuggingFaceRegistryData]
