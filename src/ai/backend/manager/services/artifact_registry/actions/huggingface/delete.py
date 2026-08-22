import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
)


@dataclass
class DeleteHuggingFaceRegistryAction(ArtifactRegistrySingleEntityAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_hugging_face_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteHuggingFaceRegistryActionResult:
    deleted_registry_id: uuid.UUID
