from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.actions.v2.ops.base import (
    BulkScopedSearchOpsAction,
    GlobalSearcherOpsAction,
)
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
from ai.backend.manager.models.login_session.row import LoginSessionRow
from ai.backend.manager.models.login_session.scopes import MyLoginSessionTarget
from ai.backend.manager.models.login_session.searchers import LoginSessionSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class GlobalSearchLoginSessionsAction(GlobalSearcherOpsAction[LoginSessionRow, LoginSessionData]):
    """Page through the login sessions of every user."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_login_sessions"


@dataclass(frozen=True)
class SearchLoginSessionsAction(BulkScopedSearchOpsAction[LoginSessionRow, LoginSessionData]):
    """Page through the login sessions of the users named, combined with OR."""

    user_ids: Sequence[UserID]
    searcher: LoginSessionSearcher

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.user_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [MyLoginSessionTarget(user_id=user_id) for user_id in self.user_ids]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_login_sessions"

    @override
    def to_searcher(self) -> LoginSessionSearcher:
        return self.searcher
