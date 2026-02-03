from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.deployment.types import DeploymentHistoryData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import SchedulingHistoryAction


@dataclass
class SearchDeploymentHistoryAction(SchedulingHistoryAction):
    """Action to search deployment history."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "deployment:history"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchDeploymentHistoryActionResult(BaseActionResult):
    """Result of searching deployment history."""

    histories: list[DeploymentHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
