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
class GetKernelAllocationBySlotAction(ResourceSlotAction):
    kernel_id: uuid.UUID
    slot_name: str

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
        return f"{self.kernel_id}:{self.slot_name}"


@dataclass
class GetKernelAllocationBySlotResult(BaseActionResult):
    item: ResourceAllocationData

    @override
    def entity_id(self) -> str | None:
        return None
