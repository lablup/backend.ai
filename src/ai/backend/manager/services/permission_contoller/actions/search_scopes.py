from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.actions.action import SearchActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import ScopeData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchScopesAction(RoleAction):
    """Action to search scopes.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    scope_type: ScopeType
    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchScopesActionResult(SearchActionResult[ScopeData]):
    pass
