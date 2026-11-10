from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class LoadContainerRegistriesAction(ContainerRegistryAction):
    registry: str
    project: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "load_container_registries"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class LoadContainerRegistriesActionResult:
    registries: list[ContainerRegistryData]

    # TODO: Add this
