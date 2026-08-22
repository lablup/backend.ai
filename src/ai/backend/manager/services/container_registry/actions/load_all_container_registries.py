from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class LoadAllContainerRegistriesAction(ContainerRegistryAction):
    @override
    @classmethod
    def action_name(cls) -> str:
        return "load_all_container_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class LoadAllContainerRegistriesActionResult:
    registries: list[ContainerRegistryData]
