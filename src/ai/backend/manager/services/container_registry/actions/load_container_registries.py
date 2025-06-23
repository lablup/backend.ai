from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class LoadContainerRegistriesAction(ContainerRegistryAction):
    registry: str
    project: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "load_multi"


@dataclass
class LoadContainerRegistriesActionResult(BaseActionResult):
    registries: list[ContainerRegistryData]

    # TODO: Add this
    @override
    def entity_id(self) -> Optional[str]:
        return None
