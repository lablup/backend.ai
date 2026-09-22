from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.models.kernel.queriers import BulkKernelQuerier
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_owner import (
    LookupBulkKernelOwnerAction,
)


@dataclass
class BulkGetKernelsAction(
    PartialBulkGetFieldOpsAction[KernelID, SessionID, KernelRow, KernelInfo]
):
    """Read the kernels the caller named, answering for each one."""

    ids: Sequence[KernelID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_kernels"

    @override
    def field_ids(self) -> Sequence[KernelID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKernelOwnerAction:
        return LookupBulkKernelOwnerAction(kernel_ids=self.ids)

    @override
    def to_querier(self) -> BulkKernelQuerier:
        return BulkKernelQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[KernelID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
