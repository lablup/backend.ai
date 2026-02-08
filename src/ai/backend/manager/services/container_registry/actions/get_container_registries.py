from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class GetContainerRegistriesAction(ContainerRegistryAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetContainerRegistriesActionResult(BaseActionResult):
    registries: Any

    @override
    def entity_id(self) -> str | None:
        return None
