from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchKernelScopedHistoryAction(BaseScopeAction):
    """Action to search the scheduling history of one kernel.

    The owning session is the authorization subject, scope, and target: kernel
    permission records are intentionally kept empty, so whoever may read the
    session may read its kernels' scheduling history. The caller resolves
    ``kernel_id -> session_id`` first (``ResolveKernelSessionAction``) and
    passes both in; ``kernel_id`` bounds the repository query.
    """

    kernel_id: KernelId
    session_id: SessionId
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.SESSION

    @override
    def scope_id(self) -> str:
        return str(self.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=str(self.session_id),
        )


@dataclass
class SearchKernelScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching the scheduling history of one kernel."""

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    kernel_id: KernelId
    session_id: SessionId

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.SESSION

    @override
    def scope_id(self) -> str:
        return str(self.session_id)
