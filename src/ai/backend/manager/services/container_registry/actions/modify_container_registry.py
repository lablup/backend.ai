from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class ModifyContainerRegistryAction(ContainerRegistryAction):
    updater: Updater[ContainerRegistryRow]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.updater.pk_value)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyContainerRegistryActionResult(BaseActionResult):
    data: ContainerRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.data.id)
