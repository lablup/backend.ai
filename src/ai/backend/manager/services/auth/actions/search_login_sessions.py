from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE, USER_SCOPE_TYPE, UserID
from ai.backend.manager.actions.v2.ops.base import (
    OperationScopeOpsAction,
    SearchGlobalOpsAction,
)
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
from ai.backend.manager.models.login_session.row import LoginSessionRow
from ai.backend.manager.models.login_session.scopes import MyLoginSessionOperationScope
from ai.backend.manager.models.login_session.searchers import LoginSessionSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class GlobalSearchLoginSessionsAction(SearchGlobalOpsAction[LoginSessionRow, LoginSessionData]):
    """Page through the login sessions of every user."""

    searcher: LoginSessionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_login_sessions"

    @override
    def to_searcher(self) -> LoginSessionSearcher:
        return self.searcher


@dataclass(frozen=True)
class SearchLoginSessionsAction(OperationScopeOpsAction[LoginSessionRow, LoginSessionData]):
    """Page through the login sessions one user owns."""

    user_id: UserID
    searcher: LoginSessionSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (MyLoginSessionOperationScope(user_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_login_sessions"

    @override
    def to_searcher(self) -> LoginSessionSearcher:
        return self.searcher
