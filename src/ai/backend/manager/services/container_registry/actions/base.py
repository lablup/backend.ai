from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ContainerRegistryAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "container_registry"


@dataclass
class ContainerRegistryBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "container_registry"
