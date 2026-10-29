"""Read of the kernel group environ rows of the named sessions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.kernel_group_environ.scopes import SessionKernelGroupEnvironTarget
from ai.backend.manager.models.kernel_group_environ.searchers import KernelGroupEnvironSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchKernelGroupEnvironsAction(
    BulkScopedSearchOpsAction[KernelGroupEnvironRow, KernelGroupEnvironData]
):
    """Page through the environ rows of the sessions' kernel groups, combined with OR.

    Every session is authorized before the read runs.
    """

    session_ids: Sequence[SessionID]
    searcher: KernelGroupEnvironSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_kernel_group_environs"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.session_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            SessionKernelGroupEnvironTarget(session_id=session_id)
            for session_id in self.session_ids
        ]

    @override
    def to_searcher(self) -> KernelGroupEnvironSearcher:
        return self.searcher
