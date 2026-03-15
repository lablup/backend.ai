import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.services.session.base import SessionScopeAction


# TODO: Make this BatchAction
@dataclass
class MatchSessionsAction(SessionScopeAction):
    """Match sessions by ID or name prefix.

    RBAC validation checks if the user has READ permission in USER scope.
    Scope is always USER scope with user_id.
    """

    id_or_name_prefix: str
    owner_access_key: AccessKey
    user_id: uuid.UUID

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.USER,
            element_id=str(self.user_id),
        )


@dataclass
class MatchSessionsActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    # session_rows: list[SessionRow]

    @override
    def entity_id(self) -> str | None:
        return None
