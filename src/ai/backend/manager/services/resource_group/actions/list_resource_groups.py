from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ResourceGroupGlobalAction


@dataclass(frozen=True)
class SearchResourceGroupsAction(ResourceGroupGlobalAction):
    """Action to search resource groups."""

    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_resource_groups"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass(frozen=True)
class SearchResourceGroupsActionResult:
    """Result of searching resource groups."""

    resource_groups: list[ResourceGroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
