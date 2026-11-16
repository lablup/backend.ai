"""Read of the kernel group resource slot rows of the named sessions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupResourceSlotData
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.kernel_group_resource_slot.scopes import (
    SessionKernelGroupResourceSlotTarget,
)
from ai.backend.manager.models.kernel_group_resource_slot.searchers import (
    KernelGroupResourceSlotSearcher,
)
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchKernelGroupResourceSlotsAction(
    BulkScopedSearchOpsAction[KernelGroupResourceSlotRow, KernelGroupResourceSlotData]
):
    """Page through the resource slot rows of the sessions' kernel groups, combined with OR.

    Every session is authorized before the read runs.
    """

    session_ids: Sequence[SessionID]
    searcher: KernelGroupResourceSlotSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_kernel_group_resource_slots"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.session_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            SessionKernelGroupResourceSlotTarget(session_id=session_id)
            for session_id in self.session_ids
        ]

    @override
    def to_searcher(self) -> KernelGroupResourceSlotSearcher:
        return self.searcher
