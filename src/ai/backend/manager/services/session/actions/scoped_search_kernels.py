"""Read of the kernels the named sessions run."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.kernel.scopes import SessionKernelTarget
from ai.backend.manager.models.kernel.searchers import KernelSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchKernelsAction(BulkScopedSearchOpsAction[KernelRow, KernelInfo]):
    """Page through the kernels of the sessions named, combined with OR.

    Every session is authorized before the read runs.
    """

    session_ids: Sequence[SessionID]
    searcher: KernelSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_kernels"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.session_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [SessionKernelTarget(session_id=session_id) for session_id in self.session_ids]

    @override
    def to_searcher(self) -> KernelSearcher:
        return self.searcher
