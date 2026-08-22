from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchKernelHistoryAction(BaseGlobalAction):
    """Action to search kernel scheduling history (admin API).

    System-wide and unscoped: authorization is the SUPERADMIN role gate rather
    than RBAC scope resolution, so this runs through ``GlobalActionProcessor``.
    The scoped counterpart stays on the RBAC path.
    """

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_kernel_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchKernelHistoryActionResult:
    """Result of searching kernel scheduling history."""

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
