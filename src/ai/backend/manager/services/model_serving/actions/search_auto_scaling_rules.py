from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
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
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_AUTO_SCALING_RULE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

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
