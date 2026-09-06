from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import KernelId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.bulk_base import BaseBulkFieldAction
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    LookupBulkKernelOwnerAction,
)


@dataclass
class BatchGetKernelResourceAllocationAction(BaseBulkFieldAction[KernelID, SessionID]):
    """Aggregate the slot amounts recorded against the kernels the caller named.

    A kernel is a row of the session running it, so the sessions owning the named
    kernels are read first and each answers for the read.
    """

    kernel_ids: list[KernelID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "batch_get_kernel_resource_allocation"

    @override
    def field_ids(self) -> Sequence[KernelID]:
        return tuple(self.kernel_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKernelOwnerAction:
        return LookupBulkKernelOwnerAction(kernel_ids=self.kernel_ids)


@dataclass
class BatchGetKernelResourceAllocationActionResult:
    data: dict[KernelId, ResourceAllocationAggregate]
