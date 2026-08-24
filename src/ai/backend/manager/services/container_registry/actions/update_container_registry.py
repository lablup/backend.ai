from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.models.container_registry.updaters import ContainerRegistryUpdater
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class UpdateContainerRegistryAction(ContainerRegistryAction):
    updater: ContainerRegistryUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_container_registry"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateContainerRegistryActionResult:
    data: ContainerRegistryData
