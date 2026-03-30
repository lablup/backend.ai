from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryModifierMeta
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistrySingleEntityAction,
    ArtifactRegistrySingleEntityActionResult,
)


@dataclass
class UpdateHuggingFaceRegistryAction(ArtifactRegistrySingleEntityAction):
    updater: Updater[HuggingFaceRegistryRow]
    meta: ArtifactRegistryModifierMeta

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ARTIFACT_REGISTRY, str(self.updater.pk_value))


@dataclass
class UpdateHuggingFaceRegistryActionResult(ArtifactRegistrySingleEntityActionResult):
    result: HuggingFaceRegistryData

    @override
    def target_entity_id(self) -> str:
        return str(self.result.id)
