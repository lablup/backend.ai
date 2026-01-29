from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.model_serving.types import (
    EndpointAutoScalingRuleData,
)
from ai.backend.manager.repositories.base import BatchQuerier

from .base import ModelServiceAction


@dataclass
class SearchAutoScalingRulesAction(ModelServiceAction):
    """Action to search endpoint auto scaling rules."""

    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_auto_scaling_rules"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchAutoScalingRulesActionResult(BaseActionResult):
    """Result of searching endpoint auto scaling rules."""

    rules: list[EndpointAutoScalingRuleData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
