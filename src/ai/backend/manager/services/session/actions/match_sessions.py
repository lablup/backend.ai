from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.common.data.entity.user import USER_SCOPE_TYPE, UserID
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.session.base import (
    SessionScopeAction,
    SessionScopeActionResult,
)


# TODO: Make this BatchAction
@dataclass
class MatchSessionsAction(SessionScopeAction):
    """Match sessions by ID or name prefix.

    RBAC validation checks if the user has READ permission in USER scope.
    Scope is always USER scope with user_id.
    """

    id_or_name_prefix: str
    owner_access_key: AccessKey
    user_id: UserID

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=USER_SCOPE_TYPE, scope_id=self.user_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "match_sessions"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class MatchSessionsActionResult(SessionScopeActionResult):
    # TODO: Add proper type
    result: Any
    # session_rows: list[SessionRow]
