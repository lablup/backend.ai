from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryCreatorMeta
from ai.backend.manager.data.huggingface_registry.types import HuggingFaceRegistryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.huggingface_registry import HuggingFaceRegistryRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.artifact_registry.actions.base import (
    ArtifactRegistryScopeAction,
    ArtifactRegistryScopeActionResult,
)


@dataclass
class CreateHuggingFaceRegistryAction(ArtifactRegistryScopeAction):
    creator: Creator[HuggingFaceRegistryRow]
    meta: ArtifactRegistryCreatorMeta

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ARTIFACT_REGISTRY, "")


@dataclass
class CreateHuggingFaceRegistryActionResult(ArtifactRegistryScopeActionResult):
    result: HuggingFaceRegistryData

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.GLOBAL

    @override
    def scope_id(self) -> str:
        return ""
