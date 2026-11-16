from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.kernel_group_environ.queriers import BulkKernelGroupEnvironQuerier
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.services.session.actions.lookup_bulk_kernel_group_environ_owner import (
    LookupBulkKernelGroupEnvironOwnerAction,
)


@dataclass(frozen=True)
class BulkGetKernelGroupEnvironsAction(
    PartialBulkGetFieldOpsAction[
        KernelGroupEnvironID, SessionID, KernelGroupEnvironRow, KernelGroupEnvironData
    ]
):
    """Read the kernel group environ rows the caller named, answering for each one."""

    ids: Sequence[KernelGroupEnvironID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_kernel_group_environs"

    @override
    def field_ids(self) -> Sequence[KernelGroupEnvironID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkKernelGroupEnvironOwnerAction:
        return LookupBulkKernelGroupEnvironOwnerAction(kernel_group_environ_ids=self.ids)

    @override
    def to_querier(self) -> BulkKernelGroupEnvironQuerier:
        return BulkKernelGroupEnvironQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[KernelGroupEnvironID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
