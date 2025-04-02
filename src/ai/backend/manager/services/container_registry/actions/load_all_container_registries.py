from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.services.image.base import ImageAction


# TODO: load_configured_registries 해당 하는 부분은 단일 액션을 만들 수 없음.
# BatchAction...
@dataclass
class LoadAllContainerRegistriesAction(ImageAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "load_all"


@dataclass
class LoadAllContainerRegistriesActionResult(BaseActionResult):
    registries: list[ContainerRegistryData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
