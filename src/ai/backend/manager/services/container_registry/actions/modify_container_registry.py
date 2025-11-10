from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import (
    ContainerRegistryData,
    ContainerRegistryModifier,
)
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class ModifyContainerRegistryAction(ContainerRegistryAction):
    id: UUID
    modifier: ContainerRegistryModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyContainerRegistryActionResult(BaseActionResult):
    data: ContainerRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return None
