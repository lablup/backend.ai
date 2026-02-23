from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_slot.types import ResourceAllocationData

from .base import ResourceSlotAction


@dataclass
class GetKernelAllocationsAction(ResourceSlotAction):
    kernel_id: uuid.UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_ALLOCATION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.kernel_id)


@dataclass
class GetKernelAllocationsResult(BaseActionResult):
    items: list[ResourceAllocationData]

    @override
    def entity_id(self) -> str | None:
        return None
