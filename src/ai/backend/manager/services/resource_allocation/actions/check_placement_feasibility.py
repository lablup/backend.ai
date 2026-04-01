from dataclasses import dataclass
from typing import override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_allocation.types import PlacementFeasibilityResult
from ai.backend.manager.services.resource_allocation.actions.base import (
    ResourceAllocationAction,
)


@dataclass
class CheckPlacementFeasibilityAction(ResourceAllocationAction):
    """Check if a given number of identical kernels can be placed in a scaling group."""

    scaling_group: str
    per_kernel_slots: ResourceSlot
    total_kernels_needed: int

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class CheckPlacementFeasibilityActionResult(BaseActionResult):
    result: PlacementFeasibilityResult

    @override
    def entity_id(self) -> str | None:
        return None
