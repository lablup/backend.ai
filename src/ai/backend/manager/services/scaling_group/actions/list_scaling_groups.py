from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.repositories.base import Querier

from .base import ScalingGroupAction


@dataclass
class SearchScalingGroupsAction(ScalingGroupAction):
    """Action to search scaling groups."""

    querier: Querier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_scaling_groups"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchScalingGroupsActionResult(BaseActionResult):
    """Result of searching scaling groups."""

    scaling_groups: list[ScalingGroupData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
