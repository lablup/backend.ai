from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass
class SearchSessionScopedHistoryAction(BaseScopeAction):
    """Action to search the scheduling history of one session.

    The history is the entity being read and the session is the scope containing it,
    so the RBAC scope chain authorizes the caller for reading history there.
    """

    session_id: SessionId
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION_HISTORY

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
class SearchSessionScopedHistoryActionResult(BaseScopeActionResult):
    """Result of searching the scheduling history of one session."""

    histories: list[SessionSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
    session_id: SessionId

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.SESSION

    @override
    def scope_id(self) -> str:
        return str(self.session_id)
