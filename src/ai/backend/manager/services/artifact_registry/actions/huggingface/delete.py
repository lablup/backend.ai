import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class DeleteHuggingFaceRegistryAction(ArtifactRegistryAction):
    registry_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.registry_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteHuggingFaceRegistryActionResult(BaseActionResult):
    deleted_registry_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.deleted_registry_id)
