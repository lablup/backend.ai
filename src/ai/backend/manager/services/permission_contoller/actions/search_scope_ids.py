from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.permission.types import ScopeIDData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class SearchScopeIDsAction(RoleAction):
    """Action to search scope IDs.

    This action is only available to superadmins.
    Permission check is performed at the API handler level.
    """

    scope_type: ScopeType
    querier: BatchQuerier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_scope_ids"


@dataclass
class SearchScopeIDsActionResult(BaseActionResult):
    """Result of searching scope IDs."""

    items: list[ScopeIDData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
