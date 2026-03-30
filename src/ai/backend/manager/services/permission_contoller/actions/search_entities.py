from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import SearchActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.entity import EntityData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchEntitiesAction(RoleAction):
    """Action to search entities within a scope.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.

    The querier contains scope conditions (scope_type, scope_id, entity_type)
    built by EntityAdapter.build_querier().
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
class SearchEntitiesActionResult(SearchActionResult[EntityData]):
    pass
