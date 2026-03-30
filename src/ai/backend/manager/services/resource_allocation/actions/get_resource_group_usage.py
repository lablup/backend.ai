from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_allocation.types import ResourceGroupUsageData
from ai.backend.manager.services.resource_allocation.actions.base import (
    ResourceAllocationAction,
)


@dataclass
class GetResourceGroupUsageAction(ResourceAllocationAction):
    rg_name: str

    @override
    def entity_id(self) -> str | None:
        return self.rg_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetResourceGroupUsageActionResult(BaseActionResult):
    usage: ResourceGroupUsageData

    @override
    def entity_id(self) -> str | None:
        return None
