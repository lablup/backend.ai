from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class LoadAllContainerRegistriesAction(ContainerRegistryAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "load_all"


@dataclass
class LoadAllContainerRegistriesActionResult(BaseActionResult):
    registries: list[ContainerRegistryData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
