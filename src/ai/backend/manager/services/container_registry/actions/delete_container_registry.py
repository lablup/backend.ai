from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class DeleteContainerRegistryAction(ContainerRegistryAction):
    purger: Purger[ContainerRegistryRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.purger.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_container_registry"


@dataclass
class DeleteContainerRegistryActionResult(BaseActionResult):
    data: ContainerRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
