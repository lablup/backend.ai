from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_slot.types import ResourceAllocationData


@dataclass(frozen=True)
class GetKernelAllocationBySlotAction(BaseSingleEntityAction):
    """Read one slot's amount on one kernel.

    The row belongs to the session the kernel runs under, which is what answers for
    the read; the kernel resolves to it through the owner lookup.
    """

    session_id: SessionID
    kernel_id: KernelID
    slot_name: str

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.session_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_kernel_allocation_by_slot"


@dataclass(frozen=True)
class GetKernelAllocationBySlotResult:
    item: ResourceAllocationData
