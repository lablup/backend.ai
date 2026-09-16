from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.types import ScopeData
from ai.backend.manager.repositories.base import BatchQuerier


@dataclass(frozen=True)
class GlobalSearchScopesAction(BaseGlobalAction):
    """Page through the scopes of one type, whichever role hangs on them."""

    scope_type: EntityType
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RoleEntityType()

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_scopes"


@dataclass(frozen=True)
class GlobalSearchScopesActionResult:
    result: SearchResult[ScopeData]
