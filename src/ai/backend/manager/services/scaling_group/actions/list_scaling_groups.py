from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ScalingGroupGlobalAction


@dataclass(frozen=True)
class SearchScalingGroupsAction(ScalingGroupGlobalAction):
    """Action to search scaling groups."""

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
class SearchScalingGroupsActionResult:
    """Result of searching scaling groups."""

    scaling_groups: list[ScalingGroupData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
