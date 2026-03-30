import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetArtifactRegistryMetasAction(ArtifactRegistryAction):
    registry_ids: list[uuid.UUID]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactRegistryMetasActionResult(BaseActionResult):
    result: list[ArtifactRegistryData]

    @override
    def entity_id(self) -> str | None:
        return None
