import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class DeleteHuggingFaceRegistryAction(ArtifactRegistryAction):
    registry_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.registry_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_huggingface_registry"


@dataclass
class DeleteHuggingFaceRegistryActionResult(BaseActionResult):
    deleted_registry_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.deleted_registry_id)
