from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.kernel.searchers import KernelSearcher


@dataclass(frozen=True)
class GlobalSearchKernelsAction(SearchGlobalOpsAction[KernelRow, KernelInfo]):
    """Page through the kernels of every session."""

    searcher: KernelSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SessionEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_kernels"

    @override
    def to_searcher(self) -> KernelSearcher:
        return self.searcher
