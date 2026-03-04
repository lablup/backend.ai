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
    """Match sessions by ID or name prefix within a scope (domain/project).

    RBAC validation checks if the user has READ permission in the target scope.
    """

    id_or_name_prefix: str
    owner_access_key: AccessKey
    _scope_type: ScopeType = ScopeType.GLOBAL  # TODO: Set from context
    _scope_id: str = ""  # TODO: Set from context

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return self._scope_type

    @override
    def scope_id(self) -> str:
        return self._scope_id

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType(self._scope_type.value),
            element_id=self._scope_id,
        )


@dataclass
class MatchSessionsActionResult(BaseActionResult):
    # TODO: Add proper type
    result: Any
    # session_rows: list[SessionRow]

    @override
    def entity_id(self) -> str | None:
        return None
