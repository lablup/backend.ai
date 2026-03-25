from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


class ArtifactRegistryAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT_REGISTRY


class ArtifactBatchRegistryAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT_REGISTRY


class ArtifactRegistryScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT_REGISTRY


class ArtifactRegistryScopeActionResult(BaseScopeActionResult):
    pass


class ArtifactRegistrySingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT_REGISTRY

    @override
    def field_data(self) -> FieldData | None:
        return None


class ArtifactRegistrySingleEntityActionResult(BaseSingleEntityActionResult):
    pass
