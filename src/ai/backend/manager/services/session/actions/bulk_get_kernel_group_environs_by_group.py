from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetNestedFieldOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.kernel_group_environ.queriers import NestedKernelGroupEnvironQuerier
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_owner import (
    LookupBulkKernelGroupOwnerAction,
)


@dataclass(frozen=True)
class BulkGetKernelGroupEnvironsByGroupAction(
    PartialBulkGetNestedFieldOpsAction[
        KernelGroupID, SessionID, KernelGroupEnvironRow, KernelGroupEnvironData
    ]
):
    """Read the environ of each kernel group the caller named, answering for each one."""

    kernel_group_ids: Sequence[KernelGroupID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_kernel_group_environs_by_group"

    @override
    def field_ids(self) -> Sequence[KernelGroupID]:
        return tuple(self.kernel_group_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKernelGroupOwnerAction:
        return LookupBulkKernelGroupOwnerAction(kernel_group_ids=self.kernel_group_ids)

    @override
    def to_querier(self) -> NestedKernelGroupEnvironQuerier:
        return NestedKernelGroupEnvironQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[KernelGroupID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            kernel_group_ids=[gid for gid in self.kernel_group_ids if gid in allowed],
        )
