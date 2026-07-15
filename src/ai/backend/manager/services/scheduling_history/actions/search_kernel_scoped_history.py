from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history.types import (
    KernelSchedulingHistorySearchScope,
)

from .base import SchedulingHistoryAction


@dataclass
class SearchKernelScopedHistoryAction(SchedulingHistoryAction):
    """Action to search kernel scheduling history within a scope.

    This is the scoped version used by entity-scoped APIs. The scope is required and
    narrows the query to one session's kernels, one kernel, or their intersection.
    """

    scope: KernelSchedulingHistorySearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.KERNEL_SCOPED_HISTORY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        # The narrower axis identifies the query best; the scope guarantees one is set.
        if self.scope.kernel_id is not None:
            return str(self.scope.kernel_id)
        return str(self.scope.session_id)


@dataclass
class SearchKernelScopedHistoryActionResult(BaseActionResult):
    """Result of searching kernel scheduling history within scope."""

    histories: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
