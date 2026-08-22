from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.session.base import (
    SessionScopeAction,
    SessionScopeActionResult,
)


@dataclass
class SearchSessionsAction(SessionScopeAction):
    """Search sessions within a scope.

    RBAC validation checks if the user has READ permission in USER scope.
    Scope is always USER scope with user_id.
    """

    querier: BatchQuerier
    user_id: UserID

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_sessions"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchSessionsActionResult(SessionScopeActionResult):
    data: list[SessionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
