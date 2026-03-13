from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


@dataclass
class ContainerRegistryAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_REGISTRY


@dataclass
class ContainerRegistryBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_REGISTRY


class ContainerRegistryScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_REGISTRY


class ContainerRegistryScopeActionResult(BaseScopeActionResult):
    pass


class ContainerRegistrySingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_REGISTRY

    @override
    def field_data(self) -> FieldData | None:
        return None


class ContainerRegistrySingleEntityActionResult(BaseSingleEntityActionResult):
    pass
