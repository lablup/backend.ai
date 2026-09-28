from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.bulk_base import BasePartialBulkFieldAction
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    LookupBulkKernelOwnerAction,
)


@dataclass
class BatchGetKernelResourceAllocationAction(BasePartialBulkFieldAction[KernelID, SessionID]):
    """Aggregate the slot amounts recorded against the kernels the caller named.

    A kernel is a row of the session running it, so the sessions owning the named
    kernels are read first and each answers for its own kernels.
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

    @override
    def narrowed_to(self, field_ids: Sequence[KernelID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            kernel_ids=[kernel_id for kernel_id in self.kernel_ids if kernel_id in allowed],
        )
