from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType
from ai.backend.common.types import KernelId
from ai.backend.manager.actions.action.bulk import BaseBulkAction, BaseBulkActionResult
from ai.backend.manager.actions.action.types import ActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate


@dataclass(frozen=True)
class KernelResourceAllocationTarget(ActionTarget):
    """Bulk-action target identifying a single kernel by ID."""

    kernel_id: KernelId

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.KERNEL,
            element_id=str(self.kernel_id),
        )


@dataclass
class BatchGetKernelResourceAllocationAction(BaseBulkAction[KernelResourceAllocationTarget]):
    """Batch-aggregate resource allocations for one or more kernels.

    Used by the GraphQL DataLoader backing ``KernelV2.resourceAllocation``; the
    kernel ids originate from already-authorized kernel nodes.
    """

    kernel_ids: list[KernelId]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.KERNEL

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def targets(self) -> Sequence[KernelResourceAllocationTarget]:
        return [KernelResourceAllocationTarget(kernel_id=kid) for kid in self.kernel_ids]


@dataclass
class BatchGetKernelResourceAllocationActionResult(BaseBulkActionResult):
    data: dict[KernelId, ResourceAllocationAggregate]

    @override
    def element_refs(self) -> list[RBACElementRef]:
        return [
            RBACElementRef(element_type=RBACElementType.KERNEL, element_id=str(kid))
            for kid in self.data
        ]
