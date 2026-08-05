from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.types import SearchableActionTarget
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.scopes import SearchScope
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history.types import (
    KernelKernelHistorySearchScope,
    SessionKernelHistorySearchScope,
)


@dataclass(frozen=True)
class KernelHistoryTarget(SearchableActionTarget):
    """One scope item of a kernel scheduling-history search.

    Each variant carries only the id its own dimension is keyed by and derives
    both the row filter and the RBAC element ref from it.
    """


@dataclass(frozen=True)
class KernelKernelHistoryTarget(KernelHistoryTarget):
    """Scope item narrowing the history to one kernel.

    Not dispatchable yet: kernels hold no RBAC permission records of their own,
    so the adapter converts a kernel scope item into a
    ``SessionKernelHistoryTarget`` on the owning session and narrows the rows
    back down with a ``kernel_id`` query condition. This is the target it must
    pass once virtual scopes land.
    """

    kernel_id: KernelId

    @override
    def to_search_scope(self) -> SearchScope:
        return KernelKernelHistorySearchScope(kernel_id=self.kernel_id)

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.KERNEL,
            element_id=str(self.kernel_id),
        )


@dataclass(frozen=True)
class SessionKernelHistoryTarget(KernelHistoryTarget):
    """Scope item covering the history of every kernel the session owns."""

    session_id: SessionId

    @override
    def to_search_scope(self) -> SearchScope:
        return SessionKernelHistorySearchScope(session_id=self.session_id)

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=str(self.session_id),
        )


@dataclass
class SearchKernelScopedHistoryAction(BaseScopeAction):
    """Action to search kernel scheduling history under one scope item."""

    # TODO: Widen to a list of targets once this becomes a bulk action; the scope
    # input already accepts several items and means them to be OR'd, but a
    # BaseScopeAction authorizes exactly one target.
    target: KernelHistoryTarget
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
        # TODO: Derive from the target once a KernelKernelHistoryTarget becomes
        # dispatchable; the session is the only scope a caller can reach today.
        return ScopeType.SESSION

    @override
    def scope_id(self) -> str:
        return self.target.to_rbac_element_ref().element_id

    @override
    def target_element(self) -> RBACElementRef:
        return self.target.to_rbac_element_ref()


@dataclass
class SearchKernelScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching kernel scheduling history under one scope item."""

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    target: KernelHistoryTarget

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.SESSION

    @override
    def scope_id(self) -> str:
        return self.target.to_rbac_element_ref().element_id
