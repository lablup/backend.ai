from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import (
    SESSION_ENTITY_TYPE,
    SESSION_SCOPE_TYPE,
    SessionID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeRef
from ai.backend.common.types import KernelId, SessionId
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.actions.v2.scope.target import SearchableScopeTarget
from ai.backend.manager.data.kernel.types import KernelSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.scopes import (
    KernelKernelHistoryOperationScope,
    SessionKernelHistoryOperationScope,
)
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass(frozen=True)
class KernelHistoryTarget(SearchableScopeTarget):
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
    pass once virtual entities land.
    """

    kernel_id: KernelId

    @override
    def to_search_scope(self) -> OperationScope:
        return KernelKernelHistoryOperationScope(kernel_id=self.kernel_id)

    @override
    def to_scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=SESSION_SCOPE_TYPE, scope_id=SessionID(self.kernel_id))


@dataclass(frozen=True)
class SessionKernelHistoryTarget(KernelHistoryTarget):
    """Scope item covering the history of every kernel the session owns."""

    session_id: SessionId

    @override
    def to_search_scope(self) -> OperationScope:
        return SessionKernelHistoryOperationScope(session_id=self.session_id)

    @override
    def to_scope_ref(self) -> ScopeRef:
        return ScopeRef(scope_type=SESSION_SCOPE_TYPE, scope_id=SessionID(self.session_id))


@dataclass
class SearchKernelScopedHistoryAction(BaseScopeAction):
    """Action to search kernel scheduling history under one scope item."""

    # TODO: Widen to a list of targets once this becomes a bulk action; the scope
    # input already accepts several items and means them to be OR'd, but a
    # BaseScopeAction authorizes exactly one target.
    target: KernelHistoryTarget
    querier: BatchQuerier

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (self.target.to_scope_ref(),)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_kernel_scoped_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchKernelScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching kernel scheduling history under one scope item."""

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    target: KernelHistoryTarget
