from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DEPLOYMENT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentHistoryData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import SchedulingHistoryAction


@dataclass
class SearchDeploymentHistoryAction(SchedulingHistoryAction):
    """Action to search deployment history (admin API)."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_deployment_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchDeploymentHistoryActionResult:
    """Result of searching deployment history."""

    histories: list[DeploymentHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
