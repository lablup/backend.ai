from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.resource_slot.types import ResourceAllocationData


@dataclass(frozen=True)
class GetKernelAllocationBySlotAction(BaseGlobalAction):
    """Read one slot's amount on one kernel.

    Global until a kernel resolves to its session: the row belongs to the session the
    kernel runs under, and there is no lookup from a kernel id to it yet.
    """

    kernel_id: uuid.UUID
    slot_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_get_kernel_allocation_by_slot"


@dataclass(frozen=True)
class GetKernelAllocationBySlotResult:
    item: ResourceAllocationData
