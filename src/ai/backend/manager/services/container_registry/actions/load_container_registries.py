from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


# TODO: load_configured_registries 해당 하는 부분은 단일 액션을 만들 수 없음.
# BatchAction...
@dataclass
class LoadContainerRegistriesAction(ContainerRegistryAction):
    registry: str
    project: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "load_multi"


@dataclass
class LoadContainerRegistriesActionResult(BaseActionResult):
    registries: list[ContainerRegistryData]

    # TODO: Add this
    @override
    def entity_id(self) -> Optional[str]:
        return None
