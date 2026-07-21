from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.types import KernelId
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchKernelScopedHistoryAction(BaseScopeAction):
    """Action to search the scheduling history of one kernel.

    The history is the entity being read and the kernel is the scope containing it,
    mirroring the other scoped searches (a role assignment within a role, a vfolder
    within a user). Authorization needs a ``kernel:history`` read grant at a scope
    covering the kernel; scope roles receive it alongside ``session`` read, since
    kernels are reached through their owning session.
    """

    kernel_id: KernelId
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.KERNEL_HISTORY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.KERNEL

    @override
    def scope_id(self) -> str:
        return str(self.kernel_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.KERNEL,
            element_id=str(self.kernel_id),
        )


@dataclass
class SearchKernelScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching the scheduling history of one kernel."""

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    kernel_id: KernelId

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.KERNEL

    @override
    def scope_id(self) -> str:
        return str(self.kernel_id)
