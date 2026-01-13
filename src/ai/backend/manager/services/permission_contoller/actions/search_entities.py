from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.entity import EntityData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchEntitiesAction(RoleAction):
    """Action to search entities within a scope.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    scope_type: ScopeType
    scope_id: str
    target_entity_type: EntityType
    querier: BatchQuerier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_entities"


@dataclass
class SearchEntitiesActionResult(BaseActionResult):
    """Result of searching entities within a scope."""

    items: list[EntityData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
