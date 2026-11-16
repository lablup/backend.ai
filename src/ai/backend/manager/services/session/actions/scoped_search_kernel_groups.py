"""Read of the kernel groups of the named sessions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupData
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.kernel_group.scopes import SessionKernelGroupTarget
from ai.backend.manager.models.kernel_group.searchers import KernelGroupSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchKernelGroupsAction(BulkScopedSearchOpsAction[KernelGroupRow, KernelGroupData]):
    """Page through the kernel groups of the sessions named, combined with OR.

    Every session is authorized before the read runs.
    """

    session_ids: Sequence[SessionID]
    searcher: KernelGroupSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_kernel_groups"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.session_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [SessionKernelGroupTarget(session_id=session_id) for session_id in self.session_ids]

    @override
    def to_searcher(self) -> KernelGroupSearcher:
        return self.searcher
