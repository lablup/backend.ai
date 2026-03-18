from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.deployment.types import DeploymentHistoryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history.types import (
    DeploymentHistorySearchScope,
)

from .base import SchedulingHistoryAction


@dataclass
class SearchDeploymentScopedHistoryAction(SchedulingHistoryAction):
    """Action to search deployment history within a deployment scope.

    This is the scoped version used by entity-scoped APIs.
    Scope is required and specifies which deployment to query history for.
    """

    scope: DeploymentHistorySearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_SCOPED_HISTORY

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return str(self.scope.deployment_id)


@dataclass
class SearchDeploymentScopedHistoryActionResult(BaseActionResult):
    """Result of searching deployment history within scope."""

    histories: list[DeploymentHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
