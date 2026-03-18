import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetArtifactRegistryMetaAction(ArtifactRegistryAction):
    registry_id: uuid.UUID | None = None
    registry_name: str | None = None

    @override
    def entity_id(self) -> str | None:
        return str(self.registry_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactRegistryMetaActionResult(BaseActionResult):
    result: ArtifactRegistryData

    @override
    def entity_id(self) -> str | None:
        return str(self.result.id)
