from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
)


@dataclass
class GetArtifactRegistryMetaAction(ArtifactRegistrySingleEntityAction):
    """Read one artifact registry by its id."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_artifact_registry_meta"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetArtifactRegistryMetaActionResult:
    result: ArtifactRegistryData
