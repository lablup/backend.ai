from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class CreateContainerRegistryAction(ContainerRegistryAction):
    creator: Creator[ContainerRegistryRow]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_container_registry"


@dataclass
class CreateContainerRegistryActionResult(BaseActionResult):
    data: ContainerRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
