from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


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
