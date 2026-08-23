from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import (
    OperationScopeOpsAction,
    SearchGlobalOpsAction,
)
from ai.backend.manager.data.auth.login_session_types import LoginHistoryData
from ai.backend.manager.models.login_session.row import LoginHistoryRow
from ai.backend.manager.models.login_session.searchers import LoginHistorySearcher
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.auth.types import MyLoginHistoryOperationScope


@dataclass(frozen=True)
class GlobalSearchLoginHistoryAction(SearchGlobalOpsAction[LoginHistoryRow, LoginHistoryData]):
    """Page through the login attempts of every user."""

    searcher: LoginHistorySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_login_history"

    @override
    def to_searcher(self) -> LoginHistorySearcher:
        return self.searcher


@dataclass(frozen=True)
class SearchLoginHistoryAction(OperationScopeOpsAction[LoginHistoryRow, LoginHistoryData]):
    """Page through the login attempts one user made."""

    user_id: UserID
    searcher: LoginHistorySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (MyLoginHistoryOperationScope(user_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_login_history"

    @override
    def to_searcher(self) -> LoginHistorySearcher:
        return self.searcher
