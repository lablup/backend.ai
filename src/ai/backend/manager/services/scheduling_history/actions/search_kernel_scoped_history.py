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
    KernelSchedulingHistoryBySessionSearchScope,
    KernelSchedulingHistorySearchScope,
)


@dataclass(frozen=True)
class KernelSchedulingHistoryTarget(SearchableActionTarget):
    """Scope item of a kernel scheduling-history search.

    The owning session is the authorization subject of every variant, so
    ``session_id`` alone decides the RBAC element ref; each variant only differs
    in how far ``to_search_scope()`` narrows the rows.
    """

    session_id: SessionId

    @override
    def to_rbac_element_ref(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.SESSION,
            element_id=str(self.session_id),
        )


@dataclass(frozen=True)
class KernelSchedulingHistoryByKernelTarget(KernelSchedulingHistoryTarget):
    """Scope item narrowing the history to one kernel of the session.

    The caller resolves ``kernel_id -> session_id`` first
    (``ResolveKernelSessionAction``) and passes both in.
    """

    kernel_id: KernelId

    @override
    def to_search_scope(self) -> SearchScope:
        return KernelSchedulingHistorySearchScope(kernel_id=self.kernel_id)


@dataclass(frozen=True)
class KernelSchedulingHistoryBySessionTarget(KernelSchedulingHistoryTarget):
    """Scope item covering the history of every kernel the session owns."""

    @override
    def to_search_scope(self) -> SearchScope:
        return KernelSchedulingHistoryBySessionSearchScope(session_id=self.session_id)


@dataclass
class SearchKernelScopedHistoryAction(BaseScopeAction):
    """Action to search kernel scheduling history within one session.

    The session is the authorization subject, scope, and target: kernel
    permission records are intentionally kept empty, so whoever may read the
    session may read its kernels' scheduling history.

    This is still a single-target scope action, so it carries exactly one
    ``KernelSchedulingHistoryTarget``.
    """

    target: KernelSchedulingHistoryTarget
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
        return str(self.target.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return self.target.to_rbac_element_ref()


@dataclass
class SearchKernelScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching kernel scheduling history within one session."""

    items: list[KernelSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    target: KernelSchedulingHistoryTarget

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.SESSION

    @override
    def scope_id(self) -> str:
        return str(self.target.session_id)
