from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import SearchActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesData,
)
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchEntityRefsAction(RoleAction):
    """Action to search entity refs (full association rows) within a scope.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    querier: BatchQuerier

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchEntityRefsActionResult(SearchActionResult[AssociationScopesEntitiesData]):
    pass
