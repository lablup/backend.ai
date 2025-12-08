from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryCreator,
    ContainerRegistryData,
)
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class CreateContainerRegistryAction(ContainerRegistryAction):
    creator: ContainerRegistryCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateContainerRegistryActionResult(BaseActionResult):
    data: ContainerRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
