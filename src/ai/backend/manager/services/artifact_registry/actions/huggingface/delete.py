import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
    ArtifactRegistrySingleEntityActionResult,
)


@dataclass
class DeleteHuggingFaceRegistryAction(ArtifactRegistrySingleEntityAction):
    registry_id: uuid.UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.registry_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ARTIFACT_REGISTRY, str(self.registry_id))


@dataclass
class DeleteHuggingFaceRegistryActionResult(ArtifactRegistrySingleEntityActionResult):
    deleted_registry_id: uuid.UUID

    @override
    def target_entity_id(self) -> str:
        return str(self.deleted_registry_id)
