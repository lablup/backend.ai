import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import ArtifactRegistryAction


@dataclass
class GetArtifactRegistryMetasAction(ArtifactRegistryAction):
    registry_ids: list[uuid.UUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_registry_metas"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactRegistryMetasActionResult:
    result: list[ArtifactRegistryData]
