from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.container_registry.base import ContainerRegistryAction


@dataclass
class GetContainerRegistriesAction(ContainerRegistryAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "get_container_registries"


@dataclass
class GetContainerRegistriesActionResult(BaseActionResult):
    # TODO: 리턴 타입 만들 것.
    registries: Any

    @override
    def entity_id(self) -> Optional[str]:
        return None
