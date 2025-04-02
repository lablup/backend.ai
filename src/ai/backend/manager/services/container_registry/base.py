from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ContainerRegistryAction(BaseAction):
    @override
    def entity_type(self):
        return "container_registry"


@dataclass
class ContainerRegistryBatchAction(BaseBatchAction):
    @override
    def entity_type(self):
        return "container_registry"
