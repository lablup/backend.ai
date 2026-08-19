from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class DeleteContainerRegistryAction(ContainerRegistryAction):
    purger: Purger[ContainerRegistryRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_container_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteContainerRegistryActionResult:
    data: ContainerRegistryData
