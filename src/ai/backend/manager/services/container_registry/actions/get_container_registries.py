from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class GetContainerRegistriesAction(ContainerRegistryAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_multi"


@dataclass
class GetContainerRegistriesActionResult(BaseActionResult):
    registries: Any

    @override
    def entity_id(self) -> Optional[str]:
        return None
