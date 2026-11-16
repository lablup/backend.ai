from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.models.kernel_group.queriers import BulkKernelGroupQuerier
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_owner import (
    LookupBulkKernelGroupOwnerAction,
)


@dataclass(frozen=True)
class BulkGetKernelGroupsAction(
    PartialBulkGetFieldOpsAction[KernelGroupID, SessionID, KernelGroupRow, KernelGroupData]
):
    """Read the kernel groups the caller named, answering for each one."""

    ids: Sequence[KernelGroupID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_kernel_groups"

    @override
    def field_ids(self) -> Sequence[KernelGroupID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKernelGroupOwnerAction:
        return LookupBulkKernelGroupOwnerAction(kernel_group_ids=self.ids)

    @override
    def to_querier(self) -> BulkKernelGroupQuerier:
        return BulkKernelGroupQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[KernelGroupID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
