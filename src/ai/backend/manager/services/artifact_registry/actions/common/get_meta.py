import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
    ArtifactRegistrySingleEntityActionResult,
)


@dataclass
class GetArtifactRegistryMetaAction(ArtifactRegistrySingleEntityAction):
    registry_id: uuid.UUID | None = None
    registry_name: str | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        if self.registry_id:
            return str(self.registry_id)
        return self.registry_name or ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ARTIFACT_REGISTRY, self.target_entity_id())


@dataclass
class GetArtifactRegistryMetaActionResult(ArtifactRegistrySingleEntityActionResult):
    result: ArtifactRegistryData

    @override
    def target_entity_id(self) -> str:
        return str(self.result.id)
